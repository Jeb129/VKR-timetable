from django.apps import AppConfig

# from api.services.constraunt.manager import ConstraintManager



class ApiConfig(AppConfig):
    name = 'api'

    # def ready(self):
    #     # Костыль, надо будет переделать. Но потом
    #     if not ConstraintManager.constraints:
    #         ConstraintManager.load()