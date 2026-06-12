import requests
from django.conf import settings

moodle_url = settings.MOODLE_URL
token = settings.MOODLE_TOKEN
teacher_role_shortnames = ['editingteacher', 'teacher', 'coursecreator']

# Для работы блока нужно создать токен с достуом к следующим методам:
# - core_user_get_users
# - core_enrol_get_users_courses
# - core_user_get_course_user_profiles


def moodle_get_user(user):
    """Поиск пользователя по email в moodle"""
    search_params = {
                "wstoken": token,
                "wsfunction": "core_user_get_users",
                "moodlewsrestformat": "json",
                "criteria[0][key]": "email",
                "criteria[0][value]": user.email,
            }
    user_data = requests.get(moodle_url, params=search_params).json()

    if not user_data.get("users"):
        return None
    
    m_id = user_data["users"][0]["id"]
    full_name = user_data["users"][0].get("fullname", "")

    return m_id,full_name

def moodle_get_profiles(moodle_user_id):
    """Поиск профилей пользователя в различных курсах"""
    courses_params = {
                "wstoken": token,
                "wsfunction": "core_enrol_get_users_courses",
                "moodlewsrestformat": "json",
                "userid": moodle_user_id,
            }
    courses = requests.get(moodle_url, params=courses_params).json()

    if not courses:
         return None
    
    profile_params = {
        "wstoken": token,
        "wsfunction": "core_user_get_course_user_profiles",
        "moodlewsrestformat": "json",
    }
    for i, course in enumerate(courses):
        profile_params[f"userlist[{i}][userid]"] = moodle_user_id
        profile_params[f"userlist[{i}][courseid]"] = course["id"]

    profiles = requests.get(moodle_url, params=profile_params).json()
    return profiles

def find_teacher_profile(profiles):
    """Поиск профиля с правами преподавателя для"""
    for profile in profiles:
        for role in profile.get('roles', []):
            if role.get('shortname') in teacher_role_shortnames:
                return profile