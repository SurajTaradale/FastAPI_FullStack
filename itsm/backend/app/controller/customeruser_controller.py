from sqlalchemy.orm import Session
from app.models.customeruser import CustomerUser
from app.models.customer_preferences import CustomerPreferences
from app.schemas.customeruserSchema import CustomerUserSchema
from app.utils import hash_password, generate_random_password
from app.core.logging import get_logger
from sqlalchemy import func
from app.core.cache import Cache
from sqlalchemy import select, or_
from math import ceil
from typing import List, Optional

logger = get_logger(__name__)
cache = Cache()


class EmailAlreadyExistsError(Exception):
    pass

class LoginAlreadyExistsError(Exception):
    pass

class CommanErrorException(Exception):
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_valid_email(email: str) -> bool:
    import re
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def email_exists(db: Session, email: str, exclude_user_id: int = None) -> bool:
    """Check if email is already taken by a different customer user."""
    query = db.query(CustomerUser.id).filter(CustomerUser.email == email)
    if exclude_user_id:
        query = query.filter(CustomerUser.id != exclude_user_id)
    return db.query(query.exists()).scalar()


def UserLoginExistsCheck(db: Session, user_login: str, user_id: int = None) -> bool:
    query = select(CustomerUser.id).where(CustomerUser.login == user_login)
    result = db.execute(query).fetchall()
    for row in result:
        existing_id = row[0]
        if not user_id or user_id != existing_id:
            return True
    return False


def set_preferences(db: Session, user_id: int, key: str, value: str):
    db.query(CustomerPreferences).filter(
        CustomerPreferences.user_id == user_id,
        CustomerPreferences.preferences_key == key,
    ).delete()
    new_pref = CustomerPreferences(
        user_id=user_id,
        preferences_key=key,
        preferences_value=value if value else None,
    )
    db.add(new_pref)
    db.commit()


def get_all_preferences(db: Session, user_id: int) -> dict:
    """FIX: user_id must be int (CustomerPreferences.user_id is a FK to customer_user.id)."""
    cache_key = f"customerpreferences:{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        stmt = select(
            CustomerPreferences.preferences_key,
            CustomerPreferences.preferences_value,
        ).where(CustomerPreferences.user_id == user_id)
        result = db.execute(stmt).all()
        if not result:
            return {}
        prefs = {row[0]: row[1] for row in result}
        cache.set(cache_key, prefs, expire=3600)
        return prefs
    except Exception as e:
        logger.error(f"Error fetching customer preferences for user_id {user_id}: {e}")
        return {}


def Delete_customer_cache(login: str = None, user_id: int = None):
    """FIX: use 'customeruser:' prefix (was incorrectly using 'user:')."""
    if login:
        cache.delete(f"customeruser:{login}")
    if user_id:
        cache.delete(f"customeruser:{user_id}")
        cache.delete(f"customerpreferences:{user_id}")


# ── CRUD ──────────────────────────────────────────────────────────────────────

def customeruser_add(db: Session, user: CustomerUserSchema, change_user_id: int):
    required_fields = ["first_name", "last_name", "login", "email", "valid_id"]
    for field in required_fields:
        if not getattr(user, field, None):
            logger.error(f"Need {field}!")
            raise CommanErrorException(f"Need {field}!")

    if not is_valid_email(user.email):
        logger.error(f"Email address ({user.email}) not valid!")
        raise CommanErrorException(f"Email address ({user.email}) not valid!")

    if email_exists(db, user.email):
        logger.error(f"Email ({user.email}) already used.")
        raise EmailAlreadyExistsError(f"Email address ({user.email}) is already used.")

    if UserLoginExistsCheck(db, user.login):
        logger.error(f"Login '{user.login}' already exists.")
        raise LoginAlreadyExistsError(f"A user with the username '{user.login}' already exists.")

    if not user.password:
        user.password = generate_random_password()

    new_user = CustomerUser(
        title=user.title,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        login=user.login,
        pw=hash_password(user.password),
        valid_id=user.valid_id,
        customer_id=user.customer_id,
        phone=user.phone,
        fax=user.fax,
        mobile=user.mobile,
        street=user.street,
        zip=user.zip,
        city=user.city,
        country=user.country,
        comments=user.comments,
        create_by=change_user_id,
        change_by=change_user_id,
        create_time=func.now(),
        change_time=func.now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_data = _build_user_data(new_user)
    cache.set(f"customeruser:{new_user.login}", user_data, expire=3600)
    cache.set(f"customeruser:{new_user.id}", user_data, expire=3600)
    return user_data


def get_customeruser_data(db: Session, identifier):
    cache_key = f"customeruser:{identifier}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    user_data = None
    if isinstance(identifier, int):
        user_data = db.query(CustomerUser).filter(CustomerUser.id == identifier).first()
    elif isinstance(identifier, str):
        user_data = db.query(CustomerUser).filter(CustomerUser.login == identifier).first()

    if user_data:
        # FIX: pass user_data.id (int), not user_data.login (str)
        preferences = get_all_preferences(db, user_data.id)
        response_data = _build_user_data(user_data, preferences=preferences)
        cache.set(f"customeruser:{user_data.login}", response_data, expire=3600)
        cache.set(f"customeruser:{user_data.id}", response_data, expire=3600)
        return response_data

    return None


def get_customeruser_hash_pwd(db: Session, login: str) -> str:
    result = db.query(CustomerUser.pw).filter(CustomerUser.login == login).first()
    return result[0] if result else None


def get_customeruser_list(db: Session, page_no: int = 1, count_per_page: int = 10):
    if page_no < 1 or count_per_page < 1:
        raise CommanErrorException("Page number and count per page must be greater than zero.")

    offset_value = (page_no - 1) * count_per_page
    total_users = db.query(CustomerUser).count()
    total_pages = ceil(total_users / count_per_page)

    stmt = select(CustomerUser).offset(offset_value).limit(count_per_page)
    result = db.execute(stmt).scalars().all()

    user_list = [_build_user_data(u) for u in result]
    return {
        "total_users": total_users,
        "total_pages": total_pages,
        "current_page": page_no,
        "users": user_list,
    }


def get_customeruser_search(
    db: Session,
    Search: Optional[str] = None,
    UserLogin: Optional[str] = None,
) -> List[dict]:
    if not Search and not UserLogin:
        raise CommanErrorException("At least one search parameter must be provided.")

    query = db.query(CustomerUser)
    if Search:
        term = f"%{Search}%"
        query = query.filter(
            or_(
                CustomerUser.first_name.ilike(term),
                CustomerUser.last_name.ilike(term),
                CustomerUser.login.ilike(term),
                CustomerUser.email.ilike(term),
            )
        )
    if UserLogin:
        query = query.filter(CustomerUser.login.ilike(f"%{UserLogin}%"))

    users = query.all()
    return [_build_user_data(u) for u in users]


def customer_user_update(db: Session, user_id: int, user: CustomerUserSchema, change_user_id: int):
    existing_user = db.query(CustomerUser).filter(CustomerUser.id == user_id).first()
    if not existing_user:
        raise CommanErrorException(f"User with ID '{user_id}' not found.")

    # Only first_name, last_name, login, email, valid_id are truly required
    required_fields = ["first_name", "last_name", "login", "email", "valid_id"]
    for field in required_fields:
        if not getattr(user, field, None):
            raise CommanErrorException(f"Need {field}!")

    if not is_valid_email(user.email):
        raise CommanErrorException(f"Email address ({user.email}) not valid!")

    # FIX: compare against the model's email column, not preferences
    if user.email != existing_user.email:
        if email_exists(db, user.email, exclude_user_id=user_id):
            raise EmailAlreadyExistsError(f"Email address ({user.email}) is already used.")

    if user.login != existing_user.login and UserLoginExistsCheck(db, user.login, user_id):
        raise LoginAlreadyExistsError(f"A user with the username '{user.login}' already exists.")

    existing_user.first_name = user.first_name
    existing_user.last_name = user.last_name
    existing_user.login = user.login
    existing_user.email = user.email
    existing_user.valid_id = user.valid_id
    existing_user.customer_id = user.customer_id
    existing_user.phone = user.phone
    existing_user.fax = user.fax
    existing_user.mobile = user.mobile
    existing_user.street = user.street
    existing_user.zip = user.zip
    existing_user.city = user.city
    existing_user.country = user.country
    existing_user.comments = user.comments
    existing_user.change_by = change_user_id
    existing_user.change_time = func.now()

    if user.password:
        existing_user.pw = hash_password(user.password)

    db.commit()
    db.refresh(existing_user)

    user_data = _build_user_data(existing_user)
    Delete_customer_cache(existing_user.login, existing_user.id)
    cache.set(f"customeruser:{existing_user.login}", user_data, expire=3600)
    cache.set(f"customeruser:{existing_user.id}", user_data, expire=3600)
    return user_data


# ── Internal helper ────────────────────────────────────────────────────────────

def _build_user_data(user: CustomerUser, preferences: dict = None) -> dict:
    data = {
        "id": user.id,
        "login": user.login,
        "title": user.title,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "valid_id": user.valid_id,
        "customer_id": user.customer_id,
        "phone": user.phone,
        "fax": user.fax,
        "mobile": user.mobile,
        "street": user.street,
        "zip": user.zip,
        "city": user.city,
        "country": user.country,
        "comments": user.comments,
        "create_by": user.create_by,
        "change_by": user.change_by,
        "create_time": user.create_time.isoformat() if user.create_time else None,
        "change_time": user.change_time.isoformat() if user.change_time else None,
    }
    if preferences is not None:
        data["preferences"] = preferences
    return data
