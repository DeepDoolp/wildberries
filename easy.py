import streamlit as st
import pandas as pd
from collections import Counter

# Категории жалоб и ключевые слова
CATEGORIES = {
    "Размер не подходит": [
         "не по размеру", "не подошла", "мала", "маленькая", "зазоры", "короткой",
        "не полностью закрывает", "не на весь экран", "прорези не совпадают", "не закрывает края",
        "меньше по диагонали",  "кривой вырез", "не совпал с камерой", "неподошли", "большие",
        "вырез под камеру", "размер"
    ],
    "Качество материала": [ "тонкая", "качество", "ужасное", "рябит", "размыто", "тоненькая", "пузырь",
        "отклеивается", "по краям", "болят глаза", "не приклеивается", "колется",
        "видно плохо", "в масле", "точки", "шлифовальная", "царапается", "не ровная",
        "углы отклеились", "остаются полосы", "не рекомендую", "края не приклеиваются",
        "задирается", "отходит"
    ],
    "Брак": ["мусор", "грязная", "царапина", "грязное", "повреждение", "дефект", "сломано",
        "брак", "треснуло", "треснула", "помятая упаковка", "стекло треснуло", "порвался"
    ],
    "Ошибка комплектации": ["вместо", "не то", "ошибка", "перепутали", "не заказывал", "гидрогелевая",
        "не полиуретановая", "пришло не то", "вырез не такой", "не соответствует",
        "андроид вместо айфон", "другой цвет", "прислали глянец", "прислали одну",
        "заказал две", "пришло на андроид", "прислали не ту", "одна плёнка", "не подходит"
    ],
    "Визуальное искажение": ["искажает", "блекло", "размыто", "всё мутно", "искажение"],
    "Функциональные проблемы": ["отпечаток", "палец не видит", "палец не срабатывает", "не реагирует",
        "не срабатывает отпечаток", "face id", "touch id", "буквы не срабатывают",
        "экран не чувствительный", "пароль не вводится", "яркость", "затеняет"],
    "Запах": ["воняет", "воняла", "пахнет", "запах", "неприятный запах", "вонь"],
    "Доставка": ["мятая", "коробка"],
    "Инструкция": ["не понятная", "сложно"],
    # Добавьте остальные категории по аналогии
}

# Функция классификации

def classify_review(text):
    text = text.lower()
    matched = []
    for cat, keywords in CATEGORIES.items():
        if any(word in text for word in keywords):
            matched.append(cat)
    return matched if matched else ["Другое"]

# Функция выбора основной категории с учётом "Другое"

def get_main_category(categories_list):
    counts = Counter(categories_list)
    common = counts.most_common()
    if common and common[0][0] == "Другое" and len(common) > 1:
        return f"Другое, {common[1][0]}"
    return common[0][0] if common else "Другое"

# Конфигурация страницы
st.set_page_config(page_title="Анализ отзывов на товары", layout="wide")
st.title("📊 Анализ отзывов на товары")

# Загрузка данных
uploaded_file = st.file_uploader("Загрузите файл с отзывами (Excel)", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name="отзывы")
    df = df[["Артикул продавца", "Количество звезд", "Текст отзыва", "Достоинства", "Недостатки"]]
    df.columns = ["model", "stars", "text", "pros_text", "cons_text"]
    df["stars"] = pd.to_numeric(df["stars"], errors='coerce')
    df["full_text"] = df[["text", "pros_text", "cons_text"]].fillna("").agg(" ".join, axis=1)
    df = df[df["full_text"].str.strip() != ""]

    # Фильтрация негативных отзывов
    df_neg = df[df["stars"] <= 4]

    # Классификация отзывов по категориям
    df_neg["categories"] = df_neg["full_text"].apply(classify_review)
    all_data = df_neg.explode("categories")

    # Топ-20 моделей по негативным отзывам с основной категорией
    st.subheader("💥 Топ-20 моделей по количеству негативных отзывов")
    bad_counts = df_neg["model"].value_counts()
    total_counts = df["model"].value_counts()
    summary_df = pd.DataFrame({
        "Негативных": bad_counts,
        "Всего": total_counts
    }).fillna(0).astype(int)
    summary_df["% Негативных"] = (summary_df["Негативных"] / summary_df["Всего"] * 100).round(1)
    main_cat = all_data.groupby("model")["categories"].apply(get_main_category)
    summary_df["Основная категория"] = main_cat
    top_summary = summary_df.sort_values("Негативных", ascending=False).head(20)
    st.dataframe(top_summary)

    # Общее распределение категорий жалоб
    st.subheader("📊 На что жалуются клиенты больше всего")
    overall_counts = all_data["categories"].value_counts().reset_index()
    overall_counts.columns = ["Категория", "Количество"]
    st.dataframe(overall_counts)

    # Детальный анализ по каждой категории
    st.subheader("🔍 Анализ по категориям")
    for _, row in overall_counts.iterrows():
        cat = row["Категория"]
        cnt = row["Количество"]
        with st.expander(f"{cat} — {cnt} отзывов"):
            sub = all_data[all_data["categories"] == cat]
            st.download_button(
                label="⬇️ Скачать все отзывы этой категории",
                data=sub[["model", "stars", "full_text"]].to_csv(index=False),
                file_name=f"{cat}_все_отзывы.csv",
                mime="text/csv"
            )
            model_counts = sub["model"].value_counts().reset_index()
            model_counts.columns = ["Модель", "Количество отзывов"]
            st.dataframe(model_counts)

            # Добавляем опцию "Все модели" и выбираем по умолчанию
            models = model_counts["Модель"].tolist()
            options = ["Все модели"] + models
            selected_model = st.selectbox(
                f"Отзывы по модели с проблемой «{cat}»",
                options,
                index=0,
                key=f"sel_{cat}"
            )

            # Показываем отзывы в зависимости от выбора
            if selected_model == "Все модели":
                model_reviews = sub
            else:
                model_reviews = sub[sub["model"] == selected_model]

            for _, r in model_reviews.iterrows():
                st.markdown(f"**⭐ {int(r['stars'])}** — {r['full_text'].strip()}")
                st.markdown("---")
