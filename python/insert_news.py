# =========================================================
# 고독사 뉴스 CSV → Oracle DB 저장
# =========================================================

import os
import sys
import csv
import re
from datetime import datetime


# =========================================================
# 프로젝트 루트 경로 추가
# =========================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BASE_DIR = os.path.dirname(
    CURRENT_DIR
)

sys.path.insert(
    0,
    BASE_DIR
)


# =========================================================
# DB 연결
# =========================================================

from database.database import connect_db


# =========================================================
# 파일 경로
# =========================================================

CSV_PATH = os.path.join(
    BASE_DIR,
    "data",
    "lonely_death_news_processed.csv"
)


# =========================================================
# 기본 설정
# =========================================================

TABLE_NAME = "LONELY_DEATH_NEWS"


# =========================================================
# CSV 값 정리
# =========================================================

def clean_value(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


# =========================================================
# 연도 변환
#
# 예:
# 2019
# 2019.0
# 2019.12.19.
# → 2019
# =========================================================

def parse_year(value):

    value = clean_value(value)

    if value is None:
        return None

    # 숫자로 시작하는 4자리 연도 추출
    match = re.search(
        r"(19|20)\d{2}",
        value
    )

    if match:
        return int(
            match.group(0)
        )

    return None


# =========================================================
# 작성일 변환
#
# CSV:
# 2019.12.19.
#
# Oracle DATE:
# 2019-12-19
# =========================================================

def parse_date(value):

    value = clean_value(value)

    if value is None:
        return None

    value = value.replace(
        " ",
        ""
    )

    # -----------------------------------------------------
    # 2019.12.19.
    # -----------------------------------------------------

    match = re.match(
        r"^(\d{4})\.(\d{1,2})\.(\d{1,2})\.?$",
        value
    )

    if match:

        year = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        day = int(
            match.group(3)
        )

        try:

            return datetime(
                year,
                month,
                day
            )

        except ValueError:

            return None


    # -----------------------------------------------------
    # 2019-12-19
    # -----------------------------------------------------

    match = re.match(
        r"^(\d{4})-(\d{1,2})-(\d{1,2})$",
        value
    )

    if match:

        year = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        day = int(
            match.group(3)
        )

        try:

            return datetime(
                year,
                month,
                day
            )

        except ValueError:

            return None


    # -----------------------------------------------------
    # 2019/12/19
    # -----------------------------------------------------

    match = re.match(
        r"^(\d{4})/(\d{1,2})/(\d{1,2})$",
        value
    )

    if match:

        year = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        day = int(
            match.group(3)
        )

        try:

            return datetime(
                year,
                month,
                day
            )

        except ValueError:

            return None


    return None


# =========================================================
# CSV 인코딩 자동 처리
# =========================================================

def open_csv():

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp949",
        "euc-kr"
    ]

    last_error = None


    for encoding in encodings:

        try:

            return open(
                CSV_PATH,
                "r",
                encoding=encoding,
                newline=""
            )

        except UnicodeDecodeError as error:

            last_error = error


    raise last_error


# =========================================================
# CSV 데이터 읽기
# =========================================================

def load_csv():

    if not os.path.exists(
        CSV_PATH
    ):

        raise FileNotFoundError(
            f"\nCSV 파일을 찾을 수 없습니다.\n"
            f"경로: {CSV_PATH}"
        )


    file = open_csv()

    reader = csv.DictReader(
        file
    )


    print(
        "\nCSV 컬럼:"
    )

    print(
        reader.fieldnames
    )


    rows = []


    for line_number, row in enumerate(
        reader,
        start=2
    ):

        year = parse_year(
            row.get("연도")
        )

        press = clean_value(
            row.get("언론사")
        )

        write_date = parse_date(
            row.get("작성일")
        )

        title = clean_value(
            row.get("기사제목")
        )

        summary = clean_value(
            row.get("기사요약")
        )

        article_url = clean_value(
            row.get("기사URL")
        )

        image_url = clean_value(
            row.get("이미지URL")
        )


        # -------------------------------------------------
        # 연도 검증
        # -------------------------------------------------

        if year is None:

            print(
                f"[경고] {line_number}번째 행 "
                f"연도 변환 실패: "
                f"{row.get('연도')}"
            )

            continue


        # -------------------------------------------------
        # 날짜가 없는 경우
        #
        # 날짜가 없어도 뉴스 자체는 저장
        # -------------------------------------------------

        rows.append({

            "year":
                year,

            "press":
                press,

            "write_date":
                write_date,

            "title":
                title,

            "summary":
                summary,

            "article_url":
                article_url,

            "image_url":
                image_url

        })


    file.close()


    return rows


# =========================================================
# DB 컬럼 확인
# =========================================================

def check_table(cursor):

    print(
        "\nLONELY_DEATH_NEWS 테이블 확인 중..."
    )


    cursor.execute(
        """
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            DATA_LENGTH
        FROM USER_TAB_COLUMNS
        WHERE TABLE_NAME = 'LONELY_DEATH_NEWS'
        ORDER BY COLUMN_ID
        """
    )


    columns = cursor.fetchall()


    if not columns:

        raise RuntimeError(
            "\nLONELY_DEATH_NEWS 테이블이 없습니다.\n"
            "먼저 Oracle에서 테이블을 생성해주세요."
        )


    print(
        "\n현재 테이블 컬럼:"
    )


    for column in columns:

        print(
            f"  {column[0]}"
            f" / {column[1]}"
            f" / {column[2]}"
        )


# =========================================================
# 데이터 삽입
# =========================================================

def insert_news():

    print(
        "======================================"
    )

    print(
        "고독사 뉴스 CSV → Oracle DB"
    )

    print(
        "======================================"
    )


    # -----------------------------------------------------
    # CSV 읽기
    # -----------------------------------------------------

    print(
        f"\nCSV 파일:"
    )

    print(
        CSV_PATH
    )


    rows = load_csv()


    print(
        f"\n읽은 뉴스 수: {len(rows)}건"
    )


    if not rows:

        print(
            "저장할 데이터가 없습니다."
        )

        return


    # -----------------------------------------------------
    # DB 연결
    # -----------------------------------------------------

    conn = connect_db()

    cursor = conn.cursor()


    try:

        print(
            "\nOracle DB 연결 성공!"
        )


        # -------------------------------------------------
        # 테이블 확인
        # -------------------------------------------------

        check_table(
            cursor
        )


        # -------------------------------------------------
        # 기존 데이터 삭제
        # -------------------------------------------------

        print(
            "\n기존 LONELY_DEATH_NEWS 데이터를 삭제합니다."
        )


        cursor.execute(
            """
            DELETE FROM LONELY_DEATH_NEWS
            """
        )


        print(
            f"삭제된 행 수: {cursor.rowcount}건"
        )


        # -------------------------------------------------
        # INSERT
        # -------------------------------------------------

        insert_sql = """
            INSERT INTO LONELY_DEATH_NEWS
            (
                NEWS_NO,
                NEWS_YEAR,
                PRESS_NAME,
                WRITE_DATE,
                TITLE,
                SUMMARY,
                ARTICLE_URL,
                IMAGE_URL
            )
            VALUES
            (
                :news_no,
                :news_year,
                :press_name,
                :write_date,
                :title,
                :summary,
                :article_url,
                :image_url
            )
        """


        # -------------------------------------------------
        # NEWS_NO 시작 번호
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                NVL(
                    MAX(NEWS_NO),
                    0
                )
            FROM LONELY_DEATH_NEWS
            """
        )


        # 기존 데이터를 삭제했기 때문에
        # 사실상 0부터 시작

        start_no = 1


        # -------------------------------------------------
        # 데이터 변환
        # -------------------------------------------------

        insert_rows = []


        for index, row in enumerate(
            rows,
            start=start_no
        ):

            insert_rows.append({

                "news_no":
                    index,

                "news_year":
                    row["year"],

                "press_name":
                    row["press"],

                "write_date":
                    row["write_date"],

                "title":
                    row["title"],

                "summary":
                    row["summary"],

                "article_url":
                    row["article_url"],

                "image_url":
                    row["image_url"]

            })


        # -------------------------------------------------
        # 대량 삽입
        # -------------------------------------------------

        print(
            "\n뉴스 데이터를 삽입합니다..."
        )


        cursor.executemany(
            insert_sql,
            insert_rows
        )


        print(
            f"삽입 완료: {len(insert_rows)}건"
        )


        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        conn.commit()


        print(
            "\nCOMMIT 완료!"
        )


        # -------------------------------------------------
        # 저장 결과 확인
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM LONELY_DEATH_NEWS
            """
        )


        count = cursor.fetchone()[0]


        print(
            f"\n현재 DB 뉴스 데이터: {count}건"
        )


        # -------------------------------------------------
        # 샘플 확인
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                NEWS_NO,
                NEWS_YEAR,
                PRESS_NAME,
                WRITE_DATE,
                TITLE
            FROM LONELY_DEATH_NEWS
            ORDER BY NEWS_NO
            FETCH FIRST 5 ROWS ONLY
            """
        )


        sample_rows = cursor.fetchall()


        print(
            "\n저장된 데이터 샘플:"
        )


        for row in sample_rows:

            print(
                "--------------------------------------"
            )

            print(
                f"번호: {row[0]}"
            )

            print(
                f"연도: {row[1]}"
            )

            print(
                f"언론사: {row[2]}"
            )

            print(
                f"작성일: {row[3]}"
            )

            print(
                f"제목: {row[4]}"
            )


    except Exception as error:

        # -------------------------------------------------
        # 오류 발생 시 롤백
        # -------------------------------------------------

        conn.rollback()


        print(
            "\n!!! 오류 발생 !!!"
        )

        print(
            error
        )


        raise


    finally:

        cursor.close()

        conn.close()


        print(
            "\nDB 연결 종료"
        )


# =========================================================
# 실행
# =========================================================

if __name__ == "__main__":

    insert_news()