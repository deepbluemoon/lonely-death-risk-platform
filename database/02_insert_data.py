import csv
import os
import sys

# =========================================================
# 프로젝트 루트를 Python 경로에 추가
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


from database.database import connect_db


# =========================================================
# 경로
# =========================================================

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


# =========================================================
# 지역명 통일
# =========================================================

def normalize_region(region):

    region = str(region).strip()

    mapping = {

        "서울": "서울특별시",
        "부산": "부산광역시",
        "대구": "대구광역시",
        "인천": "인천광역시",
        "광주": "광주광역시",
        "대전": "대전광역시",
        "울산": "울산광역시",

        "세종": "세종특별자치시",

        "경기": "경기도",
        "강원": "강원특별자치도",

        "충북": "충청북도",
        "충남": "충청남도",

        "전북": "전북특별자치도",
        "전남": "전라남도",

        "경북": "경상북도",
        "경남": "경상남도",

        "제주": "제주특별자치도",

        # 현재 프로젝트에서 사용하는 이름
        "전남광주통합특별시": "전남광주통합특별시"

    }

    return mapping.get(
        region,
        region
    )


# =========================================================
# 숫자 변환
# =========================================================

def to_number(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    # CSV에서 표시된 ** 제거
    value = value.replace("*", "")

    # 콤마 제거
    value = value.replace(",", "")

    # % 제거
    value = value.replace("%", "")

    try:

        return float(value)

    except ValueError:

        return None


# =========================================================
# 1. 고독사 통합 데이터
#
# CSV 구조
#
# 지역,
# 2019,2019,2019,2019,
# 2020,2020,2020,2020,
# 2021,2021,2021,2021
#
# 지역,
# 일반가구수,
# 1인가구비율,
# 1인가구수,
# 고독사사망자수,
# ...
#
# 모든 연도 데이터를 DB에 넣는다.
# =========================================================

def insert_lonely_death():

    path = os.path.join(
        DATA_DIR,
        "고독사_지역통합_최종.csv"
    )

    print()
    print("========================================")
    print("고독사 통합 데이터 적재")
    print("========================================")

    with open(
        path,
        "r",
        encoding="utf-8-sig"
    ) as f:

        rows = list(
            csv.reader(f)
        )


    year_row = rows[0]
    column_row = rows[1]


    # -----------------------------------------------------
    # 컬럼 위치 찾기
    # -----------------------------------------------------

    columns = {}

    for i in range(
        len(year_row)
    ):

        year = year_row[i].strip()
        column = column_row[i].strip()

        if year.isdigit() and column:

            columns[
                f"{year}_{column}"
            ] = i


    # -----------------------------------------------------
    # Oracle 연결
    # -----------------------------------------------------

    conn = connect_db()
    cursor = conn.cursor()


    # -----------------------------------------------------
    # 기존 데이터 삭제
    #
    # 재실행해도 중복 INSERT가 발생하지 않도록 함
    # -----------------------------------------------------

    cursor.execute(
        "DELETE FROM TBL_LONELY_DEATH"
    )


    # -----------------------------------------------------
    # INSERT
    #
    # 테이블 컬럼 기준
    #
    # REGION
    # Y2019_GENERAL_HOUSEHOLDS
    # Y2019_ONE_PERSON_RATIO
    # Y2019_ONE_PERSON_HOUSEHOLDS
    # Y2019_LONELY_DEATHS
    #
    # Y2020_...
    #
    # Y2021_...
    # -----------------------------------------------------

    sql = """
        INSERT INTO TBL_LONELY_DEATH (
            REGION,

            Y2019_GENERAL_HOUSEHOLDS,
            Y2019_ONE_PERSON_RATIO,
            Y2019_ONE_PERSON_HOUSEHOLDS,
            Y2019_LONELY_DEATHS,

            Y2020_GENERAL_HOUSEHOLDS,
            Y2020_ONE_PERSON_RATIO,
            Y2020_ONE_PERSON_HOUSEHOLDS,
            Y2020_LONELY_DEATHS,

            Y2021_GENERAL_HOUSEHOLDS,
            Y2021_ONE_PERSON_RATIO,
            Y2021_ONE_PERSON_HOUSEHOLDS,
            Y2021_LONELY_DEATHS
        )
        VALUES (
            :1,
            :2, :3, :4, :5,
            :6, :7, :8, :9,
            :10, :11, :12, :13
        )
    """


    count = 0


    for row in rows[2:]:

        if not row:
            continue

        raw_region = row[0].strip()

        if not raw_region:
            continue

        region = normalize_region(
            raw_region
        )


        try:

            values = [

                region,

                to_number(
                    row[columns["2019_일반가구수"]]
                ),

                to_number(
                    row[columns["2019_1인가구비율"]]
                ),

                to_number(
                    row[columns["2019_1인가구수"]]
                ),

                to_number(
                    row[columns["2019_고독사사망자수"]]
                ),

                to_number(
                    row[columns["2020_일반가구수"]]
                ),

                to_number(
                    row[columns["2020_1인가구비율"]]
                ),

                to_number(
                    row[columns["2020_1인가구수"]]
                ),

                to_number(
                    row[columns["2020_고독사사망자수"]]
                ),

                to_number(
                    row[columns["2021_일반가구수"]]
                ),

                to_number(
                    row[columns["2021_1인가구비율"]]
                ),

                to_number(
                    row[columns["2021_1인가구수"]]
                ),

                to_number(
                    row[columns["2021_고독사사망자수"]]
                )

            ]

            cursor.execute(
                sql,
                values
            )

            count += 1

        except Exception as e:

            print(
                f"[고독사 오류] {region}: {e}"
            )


    conn.commit()

    cursor.close()
    conn.close()


    print(
        f"적재 완료: {count}개 지역"
    )


# =========================================================
# 2. 미충족 의료율
#
# CSV
#
# 서울,5.3,4.8,4.4,3.8...
#
# 2019 ~ 2025 전체 저장
# =========================================================

def insert_unmet_medical():

    path = os.path.join(
        DATA_DIR,
        "지방지표_미충족의료율.csv"
    )

    print()
    print("========================================")
    print("미충족 의료율 데이터 적재")
    print("========================================")

    with open(
        path,
        "r",
        encoding="utf-8-sig"
    ) as f:

        rows = list(
            csv.reader(f)
        )


    # 두 번째 행
    # 2019.0, 2020.0 ...
    year_row = rows[1]


    year_index = {}


    for i, value in enumerate(
        year_row
    ):

        value = value.strip()

        if value.endswith(".0"):
            value = value[:-2]

        if value.isdigit():

            year_index[value] = i


    conn = connect_db()
    cursor = conn.cursor()


    # 기존 데이터 삭제
    cursor.execute(
        "DELETE FROM TBL_UNMET_MEDICAL"
    )


    # -----------------------------------------------------
    # INSERT
    # -----------------------------------------------------

    sql = """
        INSERT INTO TBL_UNMET_MEDICAL (
            REGION,
            Y2019_RATE,
            Y2020_RATE,
            Y2021_RATE,
            Y2022_RATE,
            Y2023_RATE,
            Y2024_RATE,
            Y2025_RATE
        )
        VALUES (
            :1,
            :2,
            :3,
            :4,
            :5,
            :6,
            :7,
            :8
        )
    """


    count = 0


    for row in rows[2:]:

        if not row:
            continue

        raw_region = row[0].strip()

        if not raw_region:
            continue

        region = normalize_region(
            raw_region
        )


        try:

            values = [

                region,

                to_number(
                    row[year_index["2019"]]
                ),

                to_number(
                    row[year_index["2020"]]
                ),

                to_number(
                    row[year_index["2021"]]
                ),

                to_number(
                    row[year_index["2022"]]
                ),

                to_number(
                    row[year_index["2023"]]
                ),

                to_number(
                    row[year_index["2024"]]
                ),

                to_number(
                    row[year_index["2025"]]
                )

            ]


            cursor.execute(
                sql,
                values
            )

            count += 1

        except Exception as e:

            print(
                f"[의료 오류] {region}: {e}"
            )


    conn.commit()

    cursor.close()
    conn.close()


    print(
        f"적재 완료: {count}개 지역"
    )


# =========================================================
# 3. 사회복지 종사자 데이터
#
# 파일명은 실제 CSV 파일명에 맞춰 수정
# =========================================================

def insert_welfare():

    path = os.path.join(
        DATA_DIR,
        "사회복지종사자.csv"
    )

    print()
    print("========================================")
    print("사회복지 종사자 데이터 적재")
    print("========================================")

    with open(
        path,
        "r",
        encoding="utf-8-sig"
    ) as f:

        rows = list(
            csv.reader(f)
        )


    year_row = rows[0]
    column_row = rows[1]


    # -----------------------------------------------------
    # 컬럼 위치
    # -----------------------------------------------------

    columns = {}

    for i in range(
        len(year_row)
    ):

        year = year_row[i].strip()
        column = column_row[i].strip()

        if year.isdigit() and column:

            columns[
                f"{year}_{column}"
            ] = i


    conn = connect_db()
    cursor = conn.cursor()


    # 기존 데이터 삭제
    cursor.execute(
        "DELETE FROM TBL_WELFARE"
    )


    # -----------------------------------------------------
    # 모든 연도 적재
    # -----------------------------------------------------

    sql = """
        INSERT INTO TBL_WELFARE (
            REGION,

            Y2019_SOCIAL_WORKERS,
            Y2019_POPULATION,
            Y2019_ASSIGNED_POPULATION,

            Y2020_SOCIAL_WORKERS,
            Y2020_POPULATION,
            Y2020_ASSIGNED_POPULATION,

            Y2021_SOCIAL_WORKERS,
            Y2021_POPULATION,
            Y2021_ASSIGNED_POPULATION
        )
        VALUES (
            :1,
            :2, :3, :4,
            :5, :6, :7,
            :8, :9, :10
        )
    """


    count = 0


    for row in rows[2:]:

        if not row:
            continue

        raw_region = row[0].strip()

        if not raw_region:
            continue

        region = normalize_region(
            raw_region
        )


        try:

            values = [

                region,

                to_number(
                    row[columns["2019_사회복지종사자수"]]
                ),

                to_number(
                    row[columns["2019_인구수"]]
                ),

                to_number(
                    row[columns["2019_담당인구수"]]
                ),

                to_number(
                    row[columns["2020_사회복지종사자수"]]
                ),

                to_number(
                    row[columns["2020_인구수"]]
                ),

                to_number(
                    row[columns["2020_담당인구수"]]
                ),

                to_number(
                    row[columns["2021_사회복지종사자수"]]
                ),

                to_number(
                    row[columns["2021_인구수"]]
                ),

                to_number(
                    row[columns["2021_담당인구수"]]
                )

            ]


            cursor.execute(
                sql,
                values
            )

            count += 1

        except Exception as e:

            print(
                f"[복지 오류] {region}: {e}"
            )


    conn.commit()

    cursor.close()
    conn.close()


    print(
        f"적재 완료: {count}개 지역"
    )


# =========================================================
# 전체 실행
# =========================================================

if __name__ == "__main__":

    print()
    print("########################################")
    print("# CSV → ORACLE 전체 데이터 적재")
    print("########################################")


    try:

        insert_lonely_death()

        insert_unmet_medical()

        insert_welfare()


        print()
        print("########################################")
        print("# 모든 데이터 적재 완료")
        print("########################################")


    except Exception as e:

        print()
        print("########################################")
        print("# 적재 중 오류 발생")
        print("########################################")

        print(e)