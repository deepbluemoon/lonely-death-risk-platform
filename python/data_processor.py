import pandas as pd
from pathlib import Path


# ============================================================
# CSV 경로
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = (
    BASE_DIR
    / "data"
    / "고독사_지역통합_최종.csv"
)


# ============================================================
# CSV 불러오기
# ============================================================

def load_data():

    df_raw = pd.read_csv(
        CSV_FILE,
        header=None,
        encoding="utf-8-sig"
    )

    return df_raw


# ============================================================
# 2중 컬럼 처리
# ============================================================

def prepare_data(df_raw):

    year_row = df_raw.iloc[0]

    name_row = df_raw.iloc[1]

    columns = []


    for i in range(len(df_raw.columns)):

        # 첫 번째 컬럼
        if i == 0:

            columns.append("지역")

            continue


        year = str(
            year_row.iloc[i]
        ).strip()


        name = str(
            name_row.iloc[i]
        ).strip()


        # ** 제거
        year = year.replace("*", "")

        name = name.replace("*", "")


        columns.append(
            f"{year}_{name}"
        )


    # 실제 데이터
    df = df_raw.iloc[2:].copy()


    df.columns = columns


    df = df.reset_index(drop=True)


    return df


# ============================================================
# 전체 1인가구 데이터
# ============================================================

def get_one_person_data():

    df_raw = load_data()

    df = prepare_data(
        df_raw
    )


    target = "2021_1인가구비율"


    if target not in df.columns:

        raise ValueError(
            f"{target} 컬럼이 없습니다."
        )


    result = df[
        [
            "지역",
            target
        ]
    ].copy()


    result.rename(
        columns={
            target: "1인가구비율"
        },
        inplace=True
    )


    # 숫자 변환
    result["1인가구비율"] = pd.to_numeric(
        result["1인가구비율"],
        errors="coerce"
    )


    # 지역명 정리
    result["지역"] = (
        result["지역"]
        .astype(str)
        .str.strip()
    )


    # 결측값 제거
    result = result.dropna(
        subset=[
            "지역",
            "1인가구비율"
        ]
    )


    return result


# ============================================================
# 특정 지역의 1인가구 비율
# ============================================================

def get_one_person_by_region(region):

    df = get_one_person_data()


    result = df[
        df["지역"] == region
    ]


    if result.empty:

        return None


    row = result.iloc[0]


    return {
        "지역": row["지역"],
        "1인가구비율": float(
            row["1인가구비율"]
        )
    }


# ============================================================
# 직접 실행했을 때 테스트
# ============================================================

if __name__ == "__main__":

    print(
        get_one_person_by_region(
            "서울특별시"
        )
    )