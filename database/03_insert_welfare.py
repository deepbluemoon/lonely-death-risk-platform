import csv
import os
import sys

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, BASE_DIR)

from database.database import connect_db


# =========================================================
# CSV 경로
# =========================================================

CSV_PATH = os.path.join(
    BASE_DIR,
    "data",
    "사회복지종사자.csv"
)


# =========================================================
# 지역명 통일
# =========================================================

def normalize_region(region):

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
        "제주": "제주특별자치도"
    }

    region = str(region).strip()

    return mapping.get(region, region)


# =========================================================
# 숫자 변환
# =========================================================

def to_number(value):

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    value = (
        value
        .replace(",", "")
        .replace("**", "")
    )

    try:
        return float(value)

    except ValueError:
        return None


# =========================================================
# CSV → Oracle
# =========================================================

def insert_welfare():

    # -----------------------------------------------------
    # CSV 읽기
    # -----------------------------------------------------

    with open(
        CSV_PATH,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        rows = list(
            csv.reader(f)
        )


    # -----------------------------------------------------
    # CSV 컬럼 위치
    # -----------------------------------------------------

    year_row = rows[0]
    column_row = rows[1]

    columns = {}

    for i in range(
        1,
        len(year_row)
    ):

        year = year_row[i].strip()
        column = column_row[i].strip()

        if year in (
            "2019",
            "2020",
            "2021"
        ):

            columns[
                (year, column)
            ] = i


    print("CSV 컬럼 확인 완료")
    print(columns)


    # -----------------------------------------------------
    # Oracle 연결
    # -----------------------------------------------------

    conn = connect_db()
    cursor = conn.cursor()


    # -----------------------------------------------------
    # 기존 데이터 삭제
    #
    # CSV 전체를 다시 넣기 때문에
    # 중복 방지용
    # -----------------------------------------------------

    cursor.execute(
        """
        DELETE FROM TBL_WELFARE_WORKERS
        """
    )


    # -----------------------------------------------------
    # INSERT
    # -----------------------------------------------------

    sql = """
        INSERT INTO TBL_WELFARE_WORKERS
        (
            REGION,

            Y2019_SOCIAL_WORKERS,
            Y2019_POPULATION,
            Y2019_PEOPLE_PER_WORKER,

            Y2020_SOCIAL_WORKERS,
            Y2020_POPULATION,
            Y2020_PEOPLE_PER_WORKER,

            Y2021_SOCIAL_WORKERS,
            Y2021_POPULATION,
            Y2021_PEOPLE_PER_WORKER
        )
        VALUES
        (
            :1,

            :2,
            :3,
            :4,

            :5,
            :6,
            :7,

            :8,
            :9,
            :10
        )
    """


    data = []


    # -----------------------------------------------------
    # 실제 데이터
    # -----------------------------------------------------

    for row in rows[2:]:

        if not row:
            continue


        raw_region = row[0].strip()


        if not raw_region:
            continue


        # 전체 행 제외
        if raw_region == "전체":
            continue


        region = normalize_region(
            raw_region
        )


        # -------------------------------------------------
        # 2019
        # -------------------------------------------------

        y2019_workers = to_number(
            row[
                columns[
                    ("2019", "사회복지종사자수")
                ]
            ]
        )

        y2019_population = to_number(
            row[
                columns[
                    ("2019", "인구수")
                ]
            ]
        )

        y2019_ratio = to_number(
            row[
                columns[
                    ("2019", "담당인구수")
                ]
            ]
        )


        # -------------------------------------------------
        # 2020
        # -------------------------------------------------

        y2020_workers = to_number(
            row[
                columns[
                    ("2020", "사회복지종사자수")
                ]
            ]
        )

        y2020_population = to_number(
            row[
                columns[
                    ("2020", "인구수")
                ]
            ]
        )

        y2020_ratio = to_number(
            row[
                columns[
                    ("2020", "담당인구수")
                ]
            ]
        )


        # -------------------------------------------------
        # 2021
        # -------------------------------------------------

        y2021_workers = to_number(
            row[
                columns[
                    ("2021", "사회복지종사자수")
                ]
            ]
        )

        y2021_population = to_number(
            row[
                columns[
                    ("2021", "인구수")
                ]
            ]
        )

        y2021_ratio = to_number(
            row[
                columns[
                    ("2021", "담당인구수")
                ]
            ]
        )


        # -------------------------------------------------
        # 데이터 추가
        # -------------------------------------------------

        data.append(
            (
                region,

                y2019_workers,
                y2019_population,
                y2019_ratio,

                y2020_workers,
                y2020_population,
                y2020_ratio,

                y2021_workers,
                y2021_population,
                y2021_ratio
            )
        )


    # -----------------------------------------------------
    # 한 번에 INSERT
    # -----------------------------------------------------

    cursor.executemany(
        sql,
        data
    )


    conn.commit()


    # -----------------------------------------------------
    # 결과
    # -----------------------------------------------------

    print()
    print("==============================")
    print("사회복지 데이터 적재 완료")
    print("==============================")
    print(
        "적재 지역 수:",
        len(data)
    )


    # -----------------------------------------------------
    # DB 확인
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            REGION,
            Y2019_PEOPLE_PER_WORKER,
            Y2020_PEOPLE_PER_WORKER,
            Y2021_PEOPLE_PER_WORKER
        FROM TBL_WELFARE_WORKERS
        ORDER BY REGION
        """
    )


    result = cursor.fetchall()


    print()
    print("담당인구수 확인")
    print("------------------------------")


    for row in result:

        print(
            row[0],
            "| 2019:",
            row[1],
            "| 2020:",
            row[2],
            "| 2021:",
            row[3]
        )


    print("------------------------------")
    print(
        "DB 총 지역 수:",
        len(result)
    )


    cursor.close()
    conn.close()


# =========================================================
# 실행
# =========================================================

if __name__ == "__main__":

    insert_welfare()