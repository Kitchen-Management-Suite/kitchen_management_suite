import pytest 
import sys
sys.path.append("./src")
from app import app
from app import sqlSession
from app import user, household
from  sqlalchemy.sql.expression import func

app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

def getDataForSession(**kwargs):
    """
        Gets random user from database
        Should not take more than 60 seconds

        Args:
        **kwargs: Additional keyword arguments.
            - UserID (int, optional): defines a sepcific ID to get user data for
        Returns:
            <class 'db.schema.user.User'>: User class for user
    """
    userID = kwargs.get("UserID", None)
    if userID != None:
        userProfileData = sqlSession.query(user.User).filter(user.User.UserID == userID).first()
    else:
        userProfileData = sqlSession.query(user.User).order_by(func.random()).first()
    print("User Profile Being Used for Testing: ", userProfileData)
    return userProfileData


@pytest.fixture(scope="session")
def client():
    """
        Creates a flask test client with an accurate test cookie already defined

        Returns:
            <FlaskClient <Flask 'app'>>: User class for user

    """
    client = app.test_client()
    user = getDataForSession()
    with client.session_transaction() as session:
        session["user_id"] = user.UserID
        session["username"] = user.Username
        session["logged_in"] = True
        if user.households != None:
            session["household_id"] = user.households[0].HouseholdID
    print("Created Client w Accurate Session Cookie")
    return client
