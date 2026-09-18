import sys
import os

from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    render_template
)

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database.database import connect_db


# =========================================================
# 경로
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

HTML_DIR = os.path.join(
    BASE_DIR,
    "html"
)

CSS_DIR = os.path.join(
    BASE_DIR,
    "css"
)


# =========================================================
# Flask 앱
# =========================================================

app = Flask(
    __name__,
    template_folder=HTML_DIR
)


# =========================================================
# 지역명 통일
# =========================================================

def normalize_region(region):

    region = str(region).strip()

    mapping = {

        "전국": "전국",

        "서울": "서울특별시",
        "서울특별시": "서울특별시",

        "부산": "부산광역시",
        "부산광역시": "부산광역시",

        "대구": "대구광역시",
        "대구광역시": "대구광역시",

        "인천": "인천광역시",
        "인천광역시": "인천광역시",

        "광주": "광주광역시",
        "광주광역시": "광주광역시",

        "대전": "대전광역시",
        "대전광역시": "대전광역시",

        "울산": "울산광역시",
        "울산광역시": "울산광역시",

        "세종": "세종특별자치시",
        "세종특별자치시": "세종특별자치시",

        "경기": "경기도",
        "경기도": "경기도",

        "강원": "강원특별자치도",
        "강원특별자치도": "강원특별자치도",

        "충북": "충청북도",
        "충청북도": "충청북도",

        "충남": "충청남도",
        "충청남도": "충청남도",

        "전북": "전북특별자치도",
        "전북특별자치도": "전북특별자치도",

        "전남": "전라남도",
        "전라남도": "전라남도",

        "경북": "경상북도",
        "경상북도": "경상북도",

        "경남": "경상남도",
        "경상남도": "경상남도",

        "제주": "제주특별자치도",
        "제주특별자치도": "제주특별자치도",

        # -------------------------------------------------
        # 전남광주통합특별시
        # -------------------------------------------------
        #
        # 프론트에서는 이 이름을 그대로 사용하지만
        # 기존 데이터 조회가 필요한 경우 별도 처리한다.
        #
        "전남광주": "전남광주통합특별시",
        "전남광주통합": "전남광주통합특별시",
        "전남광주통합특별시": "전남광주통합특별시"
    }

    return mapping.get(
        region,
        region
    )


# =========================================================
# 통합지역용 실제 DB 조회 지역명
# =========================================================
#
# 전남광주통합특별시는 프론트에서 사용하는 지역명이고,
# 기존 의료/고령 데이터는 전라남도 기준으로 조회한다.
#
# 다른 지역은 기존 지역명을 그대로 사용한다.
# =========================================================

def get_medical_region(region):

    if region == "전남광주통합특별시":
        return "전라남도"

    return region


def get_elderly_region(region):

    if region == "전남광주통합특별시":
        return "전라남도"

    return region


# =========================================================
# 기본 페이지
# =========================================================

@app.route("/")
def index():

    return send_from_directory(
        HTML_DIR,
        "index.html"
    )


# =========================================================
# CSS
# =========================================================

@app.route("/css/<path:filename>")
def css(filename):

    return send_from_directory(
        CSS_DIR,
        filename
    )


# =========================================================
# 종합 지역 데이터
# =========================================================

@app.route(
    "/api/region/<path:region>"
)
def region_data(region):

    # -----------------------------------------------------
    # 프론트에서 받은 지역명
    # -----------------------------------------------------

    region = normalize_region(region)

    # -----------------------------------------------------
    # 의료 / 고령 데이터의 실제 조회 지역명
    # -----------------------------------------------------

    medical_region = get_medical_region(
        region
    )

    elderly_region = get_elderly_region(
        region
    )

    # -----------------------------------------------------
    # DB 연결
    # -----------------------------------------------------

    conn = connect_db()
    cursor = conn.cursor()

    # =====================================================
    # 1인가구
    # =====================================================

    cursor.execute(
        """
        SELECT
            Y2021_ONE_PERSON_RATIO
        FROM TBL_LONELY_DEATH
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [region]
    )

    one_person_row = cursor.fetchone()

    # =====================================================
    # 미충족 의료율
    # =====================================================

    cursor.execute(
        """
        SELECT
            Y2021_RATE
        FROM TBL_UNMET_MEDICAL
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [medical_region]
    )

    medical_row = cursor.fetchone()

    # =====================================================
    # 사회복지 종사자
    # =====================================================

    cursor.execute(
        """
        SELECT
            Y2021_SOCIAL_WORKERS,
            Y2021_POPULATION,
            Y2021_PEOPLE_PER_WORKER
        FROM TBL_WELFARE_WORKERS
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [region]
    )

    welfare_row = cursor.fetchone()

    # =====================================================
    # 고령인구
    # =====================================================

    cursor.execute(
        """
        SELECT
            Y2021_AVERAGE
        FROM TBL_ELDERLY_POPULATION
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [elderly_region]
    )

    elderly_row = cursor.fetchone()

    # =====================================================
    # DB 종료
    # =====================================================

    cursor.close()
    conn.close()

    # =====================================================
    # 값 변환
    # =====================================================

    one_person = (

        float(one_person_row[0])

        if one_person_row
        and one_person_row[0] is not None

        else None
    )

    medical = (

        float(medical_row[0])

        if medical_row
        and medical_row[0] is not None

        else None
    )

    welfare_workers = (

        welfare_row[0]

        if welfare_row

        else None
    )

    welfare_population = (

        welfare_row[1]

        if welfare_row

        else None
    )

    people_per_worker = (

        float(welfare_row[2])

        if welfare_row
        and welfare_row[2] is not None

        else None
    )

    elderly = (

        float(elderly_row[0])

        if elderly_row
        and elderly_row[0] is not None

        else None
    )

    # =====================================================
    # 디버깅 로그
    # =====================================================

    print(
        "======================================"
    )

    print(
        "지역 API 조회"
    )

    print(
        "프론트 지역:",
        region
    )

    print(
        "의료 조회 지역:",
        medical_region
    )

    print(
        "고령 조회 지역:",
        elderly_region
    )

    print(
        "1인가구:",
        one_person
    )

    print(
        "미충족의료율:",
        medical
    )

    print(
        "복지종사자:",
        welfare_workers
    )

    print(
        "담당인구:",
        people_per_worker
    )

    print(
        "고령인구비율:",
        elderly
    )

    print(
        "======================================"
    )

    # =====================================================
    # JSON 반환
    # =====================================================

    return jsonify({

        "지역":
            region,

        "1인가구비율":
            one_person,

        "미충족의료율":
            medical,

        "사회복지종사자수":
            welfare_workers,

        "인구수":
            welfare_population,

        "담당인구수":
            people_per_worker,

        "고령인구비율":
            elderly,

        "기준연도":
            2021
    })


# =========================================================
# 1인가구 API
# =========================================================

@app.route(
    "/api/one-person/<path:region>"
)
def one_person(region):

    region = normalize_region(region)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            Y2021_ONE_PERSON_RATIO
        FROM TBL_LONELY_DEATH
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [region]
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:

        return jsonify({

            "지역":
                region,

            "1인가구비율":
                None
        })

    return jsonify({

        "지역":
            region,

        "1인가구비율":
            float(row[0])
    })


# =========================================================
# 미충족 의료율 API
# =========================================================

@app.route(
    "/api/unmet-medical/<path:region>"
)
def unmet_medical(region):

    region = normalize_region(region)

    # 전남광주통합특별시만 기존 전라남도 데이터 사용
    medical_region = get_medical_region(
        region
    )

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            Y2021_RATE
        FROM TBL_UNMET_MEDICAL
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [medical_region]
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:

        return jsonify({

            "지역":
                region,

            "미충족의료율":
                None
        })

    return jsonify({

        "지역":
            region,

        "미충족의료율":
            float(row[0])
    })


# =========================================================
# 복지 API
# =========================================================

@app.route(
    "/api/welfare/<path:region>"
)
def welfare(region):

    region = normalize_region(region)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            Y2021_SOCIAL_WORKERS,
            Y2021_POPULATION,
            Y2021_PEOPLE_PER_WORKER
        FROM TBL_WELFARE_WORKERS
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [region]
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:

        return jsonify({

            "지역":
                region,

            "연도":
                2021,

            "사회복지종사자수":
                None,

            "인구수":
                None,

            "담당인구수":
                None
        })

    return jsonify({

        "지역":
            region,

        "연도":
            2021,

        "사회복지종사자수":
            row[0],

        "인구수":
            row[1],

        "담당인구수":
            float(row[2])
            if row[2] is not None
            else None
    })


# =========================================================
# 고령인구 API
# =========================================================

@app.route(
    "/api/elderly/<path:region>"
)
def elderly(region):

    region = normalize_region(region)

    # 전남광주통합특별시만 기존 전라남도 데이터 사용
    elderly_region = get_elderly_region(
        region
    )

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            Y2021_AVERAGE
        FROM TBL_ELDERLY_POPULATION
        WHERE TRIM(REGION) = TRIM(:1)
        """,
        [elderly_region]
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:

        return jsonify({

            "지역":
                region,

            "고령인구비율":
                None
        })

    return jsonify({

        "지역":
            region,

        "고령인구비율":
            float(row[0])
    })


# =========================================================
# DB 전체 확인
# =========================================================

@app.route("/api/test")
def test():

    conn = connect_db()
    cursor = conn.cursor()

    # =====================================================
    # 1인가구
    # =====================================================

    cursor.execute(
        """
        SELECT
            REGION,
            Y2021_ONE_PERSON_RATIO
        FROM TBL_LONELY_DEATH
        ORDER BY REGION
        """
    )

    one_person = [

        {
            "지역":
                row[0],

            "1인가구비율":
                float(row[1])
                if row[1] is not None
                else None
        }

        for row in cursor.fetchall()
    ]

    # =====================================================
    # 의료
    # =====================================================

    cursor.execute(
        """
        SELECT
            REGION,
            Y2021_RATE
        FROM TBL_UNMET_MEDICAL
        ORDER BY REGION
        """
    )

    medical = [

        {
            "지역":
                row[0],

            "미충족의료율":
                float(row[1])
                if row[1] is not None
                else None
        }

        for row in cursor.fetchall()
    ]

    # =====================================================
    # 복지
    # =====================================================

    cursor.execute(
        """
        SELECT
            REGION,
            Y2021_SOCIAL_WORKERS,
            Y2021_POPULATION,
            Y2021_PEOPLE_PER_WORKER
        FROM TBL_WELFARE_WORKERS
        ORDER BY REGION
        """
    )

    welfare = [

        {
            "지역":
                row[0],

            "사회복지종사자수":
                row[1],

            "인구수":
                row[2],

            "담당인구수":
                float(row[3])
                if row[3] is not None
                else None
        }

        for row in cursor.fetchall()
    ]

    # =====================================================
    # 고령인구
    # =====================================================

    cursor.execute(
        """
        SELECT
            REGION,
            Y2019_AVERAGE,
            Y2020_AVERAGE,
            Y2021_AVERAGE
        FROM TBL_ELDERLY_POPULATION
        ORDER BY REGION
        """
    )

    elderly_data = [

        {
            "지역":
                row[0],

            "2019":
                float(row[1])
                if row[1] is not None
                else None,

            "2020":
                float(row[2])
                if row[2] is not None
                else None,

            "2021":
                float(row[3])
                if row[3] is not None
                else None
        }

        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return jsonify({

        "1인가구":
            one_person,

        "미충족의료율":
            medical,

        "사회복지":
            welfare,

        "고령인구":
            elderly_data
    })


# =========================================================
# 뉴스
# =========================================================

keyword_by_year = {

    "all": [
        ("노인", 876),
        ("장년", 498),
        ("어르신", 452),
        ("안부", 373),
        ("위험", 332),
        ("이웃", 299),
        ("주민", 294),
        ("발굴", 271),
        ("코로나", 270),
        ("사각지대", 261)
    ],

    "2019": [
        ("노인", 274),
        ("장년", 213),
        ("어르신", 144),
        ("문제", 140),
        ("발굴", 137),
        ("사각지대", 126),
        ("이웃", 110),
        ("발견", 107),
        ("남성", 99),
        ("위험", 98)
    ],

    "2020": [
        ("노인", 322),
        ("어르신", 181),
        ("코로나", 145),
        ("안부", 140),
        ("스마트", 132),
        ("장년", 121),
        ("이웃", 108),
        ("위험", 107),
        ("홀몸", 97),
        ("사회적 고립", 74)
    ],

    "2021": [
        ("장년", 164),
        ("안부", 150),
        ("청년", 147),
        ("위험", 127),
        ("어르신", 127),
        ("안심", 126),
        ("코로나", 125),
        ("계층", 109),
        ("사회적 고립", 94),
        ("위기", 94)
    ]
}


# =========================================================
# 키워드 글자 크기
# =========================================================

def make_keyword_data(keyword_list):

    max_count = max(
        count
        for word, count in keyword_list
    )

    min_count = min(
        count
        for word, count in keyword_list
    )

    keyword_data = []

    for word, count in keyword_list:

        if max_count == min_count:

            font_size = 24

        else:

            font_size = (
                18
                +
                (
                    (count - min_count)
                    /
                    (max_count - min_count)
                )
                * 22
            )

        keyword_data.append({

            "word":
                word,

            "count":
                count,

            "font_size":
                round(
                    font_size,
                    1
                )
        })

    return keyword_data


# =========================================================
# 뉴스 페이지
# =========================================================

@app.route("/news")
def news():

    # -----------------------------------------------------
    # 검색 조건
    # -----------------------------------------------------

    selected_year = request.args.get(
        "year",
        ""
    )

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    selected_press = request.args.get(
        "press",
        ""
    )

    selected_sort = request.args.get(
        "sort",
        "latest"
    )

    page = request.args.get(
        "page",
        1,
        type=int
    )

    if page < 1:
        page = 1

    page_size = 10

    # -----------------------------------------------------
    # DB 연결
    # -----------------------------------------------------

    conn = connect_db()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # 언론사 목록
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT DISTINCT PRESS_NAME
        FROM LONELY_DEATH_NEWS
        WHERE PRESS_NAME IS NOT NULL
        ORDER BY PRESS_NAME
        """
    )

    press_rows = cursor.fetchall()

    press_list = [
        row[0]
        for row in press_rows
    ]

    # -----------------------------------------------------
    # 검색 조건
    # -----------------------------------------------------

    conditions = [
        "SUMMARY IS NOT NULL"
    ]

    params = {}

    # -----------------------------------------------------
    # 연도
    # -----------------------------------------------------

    if selected_year:

        try:

            year_value = int(
                selected_year
            )

            conditions.append(
                "NEWS_YEAR = :news_year"
            )

            params["news_year"] = (
                year_value
            )

        except ValueError:

            selected_year = ""

    # -----------------------------------------------------
    # 검색어
    # -----------------------------------------------------

    if keyword:

        conditions.append(
            """
            (
                TITLE LIKE :keyword
                OR SUMMARY LIKE :keyword
            )
            """
        )

        params["keyword"] = (
            "%"
            + keyword
            + "%"
        )

    # -----------------------------------------------------
    # 언론사
    # -----------------------------------------------------

    if selected_press:

        conditions.append(
            "PRESS_NAME = :press_name"
        )

        params["press_name"] = (
            selected_press
        )

    where_sql = " AND ".join(
        conditions
    )

    # -----------------------------------------------------
    # 정렬
    # -----------------------------------------------------

    if selected_sort == "oldest":

        order_sql = """
            NEWS_YEAR ASC,
            WRITE_DATE ASC,
            NEWS_NO ASC
        """

    else:

        selected_sort = "latest"

        order_sql = """
            NEWS_YEAR DESC,
            WRITE_DATE DESC,
            NEWS_NO DESC
        """

    # -----------------------------------------------------
    # 전체 뉴스 수
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM LONELY_DEATH_NEWS
        WHERE SUMMARY IS NOT NULL
        """
    )

    total_count = cursor.fetchone()[0]

    # -----------------------------------------------------
    # 검색 결과 수
    # -----------------------------------------------------

    count_sql = f"""
        SELECT COUNT(*)
        FROM LONELY_DEATH_NEWS
        WHERE {where_sql}
    """

    cursor.execute(
        count_sql,
        params
    )

    result_count = cursor.fetchone()[0]

    # -----------------------------------------------------
    # 페이지 수
    # -----------------------------------------------------

    if result_count == 0:

        total_pages = 1

    else:

        total_pages = (
            result_count
            + page_size
            - 1
        ) // page_size

    if page > total_pages:

        page = total_pages

    # -----------------------------------------------------
    # 페이지 범위
    # -----------------------------------------------------

    start_row = (
        (page - 1)
        * page_size
        + 1
    )

    end_row = (
        page
        * page_size
    )

    # -----------------------------------------------------
    # 뉴스 조회
    # -----------------------------------------------------

    news_sql = f"""
        SELECT *
        FROM (

            SELECT
                NEWS_DATA.*,
                ROWNUM AS RN

            FROM (

                SELECT
                    NEWS_NO,
                    NEWS_YEAR,
                    PRESS_NAME,
                    WRITE_DATE,
                    TITLE,
                    SUMMARY,
                    ARTICLE_URL,
                    IMAGE_URL

                FROM LONELY_DEATH_NEWS

                WHERE {where_sql}

                ORDER BY
                    {order_sql}

            ) NEWS_DATA

            WHERE ROWNUM <= :end_row

        )

        WHERE RN >= :start_row
    """

    news_params = params.copy()

    news_params["end_row"] = end_row

    news_params["start_row"] = start_row

    cursor.execute(
        news_sql,
        news_params
    )

    news_list = cursor.fetchall()

    # -----------------------------------------------------
    # 페이지 번호
    # -----------------------------------------------------

    start_page = max(
        1,
        page - 2
    )

    end_page = min(
        total_pages,
        page + 2
    )

    page_numbers = list(
        range(
            start_page,
            end_page + 1
        )
    )

    # -----------------------------------------------------
    # 키워드
    # -----------------------------------------------------

    if selected_year in keyword_by_year:

        current_keywords = (
            keyword_by_year[
                selected_year
            ]
        )

    else:

        current_keywords = (
            keyword_by_year["all"]
        )

    keyword_data = make_keyword_data(
        current_keywords
    )

    # -----------------------------------------------------
    # DB 종료
    # -----------------------------------------------------

    cursor.close()
    conn.close()

    # -----------------------------------------------------
    # 뉴스 HTML
    # -----------------------------------------------------

    return render_template(

        "news.html",

        news_list=news_list,

        total_count=total_count,

        result_count=result_count,

        selected_year=selected_year,

        keyword=keyword,

        selected_press=selected_press,

        selected_sort=selected_sort,

        press_list=press_list,

        keyword_data=keyword_data,

        page=page,

        total_pages=total_pages,

        page_numbers=page_numbers
    )


# =========================================================
# 실행
# =========================================================

if __name__ == "__main__":

    print(
        "======================================"
    )

    print(
        "고독사 예방 분석 플랫폼"
    )

    print(
        "Oracle DB 연동 모드"
    )

    print(
        "뉴스 페이지: /news"
    )

    print(
        "======================================"
    )

    app.run(
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
