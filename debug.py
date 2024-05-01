import pandas as pd

# Sample DataFrame
data = {
    "A": [1, 2, 3, 4, 5],
    "B": [6, 7, 8, 9, 10],
    "C": [11, 12, 13, 14, 15],
    "D": [16, 17, 18, 19, 20],
}

df = pd.DataFrame(data)


def split_dataframe(df):
    num_rows, num_cols = df.shape
    smaller_num_rows = num_rows // 2
    smaller_num_cols = num_cols // 2
    df1 = df.iloc[:smaller_num_rows, :smaller_num_cols]
    df2 = df.iloc[:smaller_num_rows, smaller_num_cols:]
    df3 = df.iloc[smaller_num_rows:, :smaller_num_cols]
    df4 = df.iloc[smaller_num_rows:, smaller_num_cols:]
    return df1, df2, df3, df4


df1, df2, df3, df4 = split_dataframe(df)

print("DataFrame 1:")
print(df1)
print("\nDataFrame 2:")
print(df2)
print("\nDataFrame 3:")
print(df3)
print("\nDataFrame 4:")
print(df4)
