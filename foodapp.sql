-- foodapp.sql 파일 (SQL 코드)

DROP TABLE IF EXISTS foods;

CREATE TABLE foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 ID, 자동으로 증가
    name TEXT NOT NULL UNIQUE           -- 음식 이름, 비어있으면 안 되고 같은 이름 중복 불가
);
