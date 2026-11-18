
from pathlib import Path
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    StratifiedKFold
)

from sklearn.pipeline import Pipeline, FeatureUnion

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.naive_bayes import MultinomialNB, ComplementNB

from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    make_scorer
)


# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "emails.csv"

MODEL_PATH = BASE_DIR / "spam_model.joblib"

GRAPH_PATH = BASE_DIR / "confusion_matrix.png"


# ==========================================
# 2. MAIN TRAINING FUNCTION
# ==========================================

def train():

    print("\n====================================")
    print(" MAILSHIELD - MODEL TRAINING")
    print("====================================\n")

    # --------------------------------------
    # LOAD DATASET
    # --------------------------------------

    print("Loading dataset...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    df = df.dropna(subset=["text", "label"])

    df["text"] = df["text"].astype(str).str.strip()

    df["label"] = (
        df["label"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df = df[df["label"].isin(["spam", "ham"])]

    df = df[df["text"].str.len() > 10]

    df = df.drop_duplicates(subset=["text"])

    if df["label"].nunique() != 2:
        raise ValueError(
            "Dataset must contain both spam and ham labels."
        )

    print("\nDataset loaded successfully!")

    print("Total emails:", len(df))

    print("\nClass distribution:")
    print(df["label"].value_counts())


    # --------------------------------------
    # SPLIT DATASET
    # --------------------------------------

    print("\nSplitting dataset...")

    X = df["text"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print("Training emails:", len(X_train))
    print("Testing emails:", len(X_test))


    # --------------------------------------
    # FEATURE EXTRACTION
    # WORD + CHARACTER TF-IDF
    # --------------------------------------

    print("\nBuilding TF-IDF feature pipeline...")

    features = FeatureUnion([

        (
            "word_tfidf",

            TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                max_features=80000,
                sublinear_tf=True
            )
        ),

        (
            "char_tfidf",

            TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=2,
                max_features=60000,
                sublinear_tf=True
            )
        )

    ])


    # --------------------------------------
    # BASE PIPELINE
    # --------------------------------------

    pipeline = Pipeline([

        ("features", features),

        ("classifier", MultinomialNB())

    ])


    # --------------------------------------
    # COMPARE ML ALGORITHMS
    # --------------------------------------

    param_grid = [

        {
            "classifier": [
                MultinomialNB()
            ],

            "classifier__alpha": [
                0.1,
                0.5,
                1.0
            ]
        },

        {
            "classifier": [
                ComplementNB()
            ],

            "classifier__alpha": [
                0.1,
                0.5,
                1.0
            ]
        },

        {
            "classifier": [
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced"
                )
            ],

            "classifier__C": [
                0.5,
                1.0,
                2.0
            ]
        }

    ]


    # --------------------------------------
    # CROSS VALIDATION
    # --------------------------------------

    cv = StratifiedKFold(
        n_splits=3,
        shuffle=True,
        random_state=42
    )

    spam_f1 = make_scorer(
        f1_score,
        pos_label="spam"
    )


    # --------------------------------------
    # GRID SEARCH
    # --------------------------------------

    print("\n====================================")
    print(" COMPARING ML ALGORITHMS")
    print("====================================\n")

    search = GridSearchCV(

        estimator=pipeline,

        param_grid=param_grid,

        scoring=spam_f1,

        cv=cv,

        n_jobs=1,

        verbose=1,

        refit=True

    )

    search.fit(X_train, y_train)

    best_model = search.best_estimator_


    # --------------------------------------
    # BEST MODEL
    # --------------------------------------

    print("\n====================================")
    print(" BEST MODEL SELECTED")
    print("====================================")

    print(
        "Algorithm:",
        best_model.named_steps["classifier"]
    )

    print(
        "Best parameters:",
        search.best_params_
    )

    print(
        f"Cross-validation Spam F1: {search.best_score_:.4f}"
    )


    # --------------------------------------
    # FINAL TESTING
    # --------------------------------------

    print("\n====================================")
    print(" FINAL MODEL EVALUATION")
    print("====================================")

    predictions = best_model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        pos_label="spam",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        pos_label="spam",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        pos_label="spam",
        zero_division=0
    )


    # --------------------------------------
    # PRINT PERFORMANCE
    # --------------------------------------

    print("\n========== PERFORMANCE ==========")

    print(f"Accuracy:  {accuracy * 100:.2f}%")

    print(f"Precision: {precision * 100:.2f}%")

    print(f"Recall:    {recall * 100:.2f}%")

    print(f"F1 Score:  {f1 * 100:.2f}%")

    print("\n========== CLASSIFICATION REPORT ==========")

    print(
        classification_report(
            y_test,
            predictions,
            labels=["ham", "spam"],
            target_names=["Not Spam", "Spam"],
            zero_division=0
        )
    )


    # --------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=["ham", "spam"]
    )

    print("\n========== CONFUSION MATRIX ==========")

    print(cm)

    display = ConfusionMatrixDisplay(

        confusion_matrix=cm,

        display_labels=[
            "Not Spam",
            "Spam"
        ]

    )

    display.plot(cmap="Blues")

    plt.title("MailShield - Spam Detection")

    plt.tight_layout()

    plt.savefig(GRAPH_PATH, dpi=300)

    plt.close()


    # --------------------------------------
    # SAVE BEST MODEL
    # --------------------------------------

    joblib.dump(
        best_model,
        MODEL_PATH
    )

    print("\n====================================")

    print(" TRAINING COMPLETED SUCCESSFULLY")

    print("====================================")

    print("\nModel saved at:", MODEL_PATH)

    print("Graph saved at:", GRAPH_PATH)

    print("\nMailShield model is ready!")


# ==========================================
# 3. EXECUTION
# ==========================================

if __name__ == "__main__":

    train()
