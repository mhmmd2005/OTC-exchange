import requests

from django.conf import settings


class EhrazAPIError(Exception):
    pass


class EhrazService:
    BASE_URL = settings.EHRAZ_API_BASE_URL
    TOKEN = settings.EHRAZ_API_TOKEN

    @classmethod
    def _headers(cls):
        return {
            "Authorization": f"Token {cls.TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @classmethod
    def _post(cls, endpoint, payload):
        try:
            response = requests.post(
                f"{cls.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}",
                json=payload,
                headers=cls._headers(),
                timeout=15,
            )
        except requests.RequestException as exc:
            raise EhrazAPIError(
                "ارتباط با سرویس احراز هویت برقرار نشد."
            ) from exc

        if not response.ok:
            raise EhrazAPIError(
                "سرویس احراز هویت پاسخ نامعتبر برگرداند."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise EhrazAPIError(
                "پاسخ سرویس احراز هویت معتبر نیست."
            ) from exc

        return data

    @classmethod
    def match_national_with_mobile(
        cls,
        national_code,
        mobile_number,
    ):
        return cls._post(
            "/match/national-with-mobile",
            {
                "nationalCode": national_code,
                "mobileNumber": mobile_number,
            },
        )

    @classmethod
    def identity_similarity(
        cls,
        national_code,
        birth_date,
        first_name,
        last_name,
        full_name,
        father_name,
    ):
        return cls._post(
            "/info/identity-similarity",
            {
                "nationalCode": national_code,
                "birthDate": birth_date,
                "firstName": first_name,
                "lastName": last_name,
                "fullName": full_name,
                "fatherName": father_name,
            },
        )

    @classmethod
    def match_card_with_national(
        cls,
        card_number,
        national_code,
        birth_date,
    ):
        return cls._post(
            "/match/card-with-national",
            {
                "cardNumber": card_number,
                "nationalCode": national_code,
                "birthDate": birth_date,
            },
        )