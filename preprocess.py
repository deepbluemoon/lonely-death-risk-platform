import pandas as pd


df = pd.read_csv('data/201912_202112_주민등록인구기타현황(인구증감)_연간.csv')


# 지역 고유번호 제거
df["행정구역"] = (
    df["행정구역"]
    .str.replace(r"\s*\(\d+\)\s*$", "", regex=True)
    .str.strip()
)

# 숫자 컬럼 콤마 제거 + int 변환
numeric_cols = df.columns.drop("행정구역")

for col in numeric_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df[col] = pd.to_numeric(df[col]).astype(int)

df = df.to_csv("data/201912_202112_주민등록인구기타현황_전처리.csv", index=False)
