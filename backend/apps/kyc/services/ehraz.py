from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings


class EhrazAPIError(Exception):
    pass


class EhrazService:
    BASE_URL = settings.EHRAZ_API_BASE_URL
    TOKEN = settings.EHRAZ_API_TOKEN
    IDENTITY_SIMILARITY_FIELDS = (
        "firstNameSimilarityPercentage",
        "lastNameSimilarityPercentage",
        "fullNameSimilarityPercentage",
        "fatherNameSimilarityPercentage",
    )

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

        message_from_core = data.get("MessageFromCore")

        if isinstance(message_from_core, dict):
            core_message = message_from_core.get("message")
            core_code = message_from_core.get("code")

            if core_message:
                raise EhrazAPIError(
                    f"{core_message}"
                    if not core_code
                    else f"{core_message} ({core_code})"
                )

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
    def identity_similarity_matches(
            cls,
            result,
            threshold=100,
    ):
        if not isinstance(result, dict):
            raise EhrazAPIError(
                "پاسخ تطبیق اطلاعات هویتی معتبر نیست."
            )

        data = result

        if not all(
                field in data
                for field in cls.IDENTITY_SIMILARITY_FIELDS
        ):
            nested = data.get("data")

            if isinstance(nested, dict):
                data = nested

        print(
            "EHRAZ IDENTITY SIMILARITY DATA:",
            {
                field: data.get(field)
                for field in cls.IDENTITY_SIMILARITY_FIELDS
            },
        )

        for field in cls.IDENTITY_SIMILARITY_FIELDS:
            if field not in data:
                raise EhrazAPIError(
                    "پاسخ تطبیق اطلاعات هویتی ناقص است."
                )

        try:
            values = [
                Decimal(
                    str(data[field])
                    .replace("%", "")
                    .strip()
                )
                for field in cls.IDENTITY_SIMILARITY_FIELDS
            ]
        except (
                InvalidOperation,
                TypeError,
                ValueError,
        ) as exc:
            raise EhrazAPIError(
                "مقادیر تطبیق اطلاعات هویتی معتبر نیستند."
            ) from exc

        matched = all(
            value >= Decimal(str(threshold))
            for value in values
        )

        print(
            "EHRAZ IDENTITY SIMILARITY VALUES:",
            {
                field: value
                for field, value in zip(
                cls.IDENTITY_SIMILARITY_FIELDS,
                values,
            )
            },
        )
        print("EHRAZ IDENTITY THRESHOLD:", threshold)
        print("EHRAZ IDENTITY MATCHED:", matched)

        return matched

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

    @classmethod
    def match_iban_with_national(
            cls,
            iban,
            national_code,
            birth_date,
    ):
        return cls._post(
            "/match/iban-with-national",
            {
                "iban": iban,
                "nationalCode": national_code,
                "birthDate": birth_date,
            },
        )
