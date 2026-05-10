from pyswip import Prolog
from datetime import date

prolog = Prolog()
prolog.consult("smart_study.pl")


def get_study_hours(difficulty, priority, exam_date):
    today = date.today()
    days_left = (exam_date - today).days

    if days_left < 0:
        days_left = 0

    query = f"calculate_hours({difficulty},{priority},{days_left},Hours)"
    result = list(prolog.query(query))

    if result:
        return result[0]["Hours"]
    return 1


# Example test
if __name__ == "__main__":
    exam = date(2025, 12, 30)
    hours = get_study_hours('high', 'high', exam)
    print(f"Recommended study hours: {hours}")
