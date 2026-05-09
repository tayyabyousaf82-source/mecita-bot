import os

from bcncita import CustomerProfile, DocType, Office, OperationType, Province, try_cita


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str):
    value = os.getenv(name, "").strip()
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def env_enum(enum_cls, name: str, default=None):
    value = os.getenv(name)
    if not value:
        return default
    value = value.strip()
    if value in enum_cls.__members__:
        return enum_cls[value]
    return enum_cls(value)


if __name__ == "__main__":
    province = env_enum(Province, "PROVINCE", Province.BARCELONA)
    operation_code = env_enum(OperationType, "OPERATION_CODE", OperationType.TOMA_HUELLAS)
    doc_type = env_enum(DocType, "DOC_TYPE", DocType.PASSPORT)

    office_values = env_list("OFFICES")
    offices = []
    for value in office_values:
        if value in Office.__members__:
            offices.append(Office[value])
        else:
            offices.append(Office(value))

    except_office_values = env_list("EXCEPT_OFFICES")
    except_offices = []
    for value in except_office_values:
        if value in Office.__members__:
            except_offices.append(Office[value])
        else:
            except_offices.append(Office(value))

    customer = CustomerProfile(
        anticaptcha_api_key=os.getenv("2CAPTCHA_API_KEY") or None,
        auto_captcha=env_bool("AUTO_CAPTCHA", False),
        auto_office=env_bool("AUTO_OFFICE", True),
        chrome_driver_path=os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"),
        save_artifacts=env_bool("SAVE_ARTIFACTS", False),
        province=province,
        operation_code=operation_code,
        doc_type=doc_type,
        doc_value=os.environ["DOC_VALUE"],
        country=os.getenv("COUNTRY", "RUSIA"),
        name=os.environ["NAME"],
        year_of_birth=os.getenv("YEAR_OF_BIRTH") or None,
        phone=os.environ["PHONE"],
        email=os.environ["EMAIL"],
        min_date=os.getenv("MIN_DATE") or None,
        max_date=os.getenv("MAX_DATE") or None,
        min_time=os.getenv("MIN_TIME") or None,
        max_time=os.getenv("MAX_TIME") or None,
        sms_webhook_token=os.getenv("SMS_WEBHOOK_TOKEN") or None,
        reason_or_type=os.getenv("REASON_OR_TYPE", "solicitud de asilo"),
        offices=offices,
        except_offices=except_offices,
    )

    cycles = int(os.getenv("CYCLES", "200"))
    try_cita(context=customer, cycles=cycles)
