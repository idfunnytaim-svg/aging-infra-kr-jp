-- 원본 CSV(data/raw/) 7개를 있는 그대로 담아둘 raw_* 테이블
-- 컬럼명·값은 CSV 헤더와 완전히 동일하게 둔다 (정제는 다음 단계 SQL에서 함)

DROP TABLE IF EXISTS raw_estat_A;
CREATE TABLE raw_estat_A (
    prefecture TEXT,
    cat01_name TEXT,
    time_name TEXT,
    value TEXT
);

DROP TABLE IF EXISTS raw_estat_I;
CREATE TABLE raw_estat_I (
    prefecture TEXT,
    cat01_name TEXT,
    time_name TEXT,
    value TEXT
);

DROP TABLE IF EXISTS raw_estat_J;
CREATE TABLE raw_estat_J (
    prefecture TEXT,
    cat01_name TEXT,
    time_name TEXT,
    value TEXT
);

DROP TABLE IF EXISTS raw_kosis_aging;
CREATE TABLE raw_kosis_aging (
    region TEXT,
    year INTEGER,
    item TEXT,
    value TEXT
);

DROP TABLE IF EXISTS raw_kosis_beds;
CREATE TABLE raw_kosis_beds (
    region TEXT,
    year INTEGER,
    item TEXT,
    value TEXT
);

DROP TABLE IF EXISTS raw_kosis_care;
CREATE TABLE raw_kosis_care (
    region TEXT,
    category2 TEXT,
    year INTEGER,
    item TEXT,
    value TEXT
);

DROP TABLE IF EXISTS raw_kosis_regpop;
CREATE TABLE raw_kosis_regpop (
    region TEXT,
    year INTEGER,
    item TEXT,
    value TEXT
);

-- 일본 도도부현 한자 표기 -> 한글 표기 매핑표
-- (scripts/preprocess_and_load.py의 JP_PREF_KR 딕셔너리와 완전히 동일한 47행)
DROP TABLE IF EXISTS map_jp_prefecture;
CREATE TABLE map_jp_prefecture (
    prefecture_local TEXT PRIMARY KEY,
    region_name_kr TEXT
);

INSERT INTO map_jp_prefecture (prefecture_local, region_name_kr) VALUES
('北海道', '홋카이도'), ('青森県', '아오모리현'), ('岩手県', '이와테현'), ('宮城県', '미야기현'),
('秋田県', '아키타현'), ('山形県', '야마가타현'), ('福島県', '후쿠시마현'), ('茨城県', '이바라키현'),
('栃木県', '도치기현'), ('群馬県', '군마현'), ('埼玉県', '사이타마현'), ('千葉県', '지바현'),
('東京都', '도쿄도'), ('神奈川県', '가나가와현'), ('新潟県', '니가타현'), ('富山県', '도야마현'),
('石川県', '이시카와현'), ('福井県', '후쿠이현'), ('山梨県', '야마나시현'), ('長野県', '나가노현'),
('岐阜県', '기후현'), ('静岡県', '시즈오카현'), ('愛知県', '아이치현'), ('三重県', '미에현'),
('滋賀県', '시가현'), ('京都府', '교토부'), ('大阪府', '오사카부'), ('兵庫県', '효고현'),
('奈良県', '나라현'), ('和歌山県', '와카야마현'), ('鳥取県', '돗토리현'), ('島根県', '시마네현'),
('岡山県', '오카야마현'), ('広島県', '히로시마현'), ('山口県', '야마구치현'), ('徳島県', '도쿠시마현'),
('香川県', '가가와현'), ('愛媛県', '에히메현'), ('高知県', '고치현'), ('福岡県', '후쿠오카현'),
('佐賀県', '사가현'), ('長崎県', '나가사키현'), ('熊本県', '구마모토현'), ('大分県', '오이타현'),
('宮崎県', '미야자키현'), ('鹿児島県', '가고시마현'), ('沖縄県', '오키나와현');
