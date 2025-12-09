import conftest 
import pytest

#Use the following code snippit to get debug info about session
#    # with client.session_transaction() as sess:
#    #     print(sess.get('user_id'))
        
def test_openfoodfacts_search(client):
    """
        Test of the open food facts api page
        Should not take more than 60 seconds

        Args:
        arg1: client (<FlaskClient <Flask 'app'>>) - Test client 
        
        Returns:
            A passed or failed assertion
    """
    formData = {
        "search_input": "Grilled Cheese",
        "MealType": "Breakfast"
    }
    response = client.post('/api_search_item_name', data=formData, content_type='application/x-www-form-urlencoded')
    assert response.status_code == 200

def test_addion_to_user_nutrition(client):
    """
        Test of adding an item to the users food log
        Should not take more than 2 seconds

        Args:
            arg1: client (<FlaskClient <Flask 'app'>>) - Test client 
        
        Returns:
            A passed or failed assertion
    """
    formData = {
        "itemName": "Test Food Item",
        "itemKCal": 1,
        "itemProtein": 1,
        "itemCarbs": 1,
        "itemFat": 1,
        "itemFiber": 1,
        "itemSugar": 1,
        "itemSodium": 1
    }
    response = client.post('/calorieTracking', data=formData, content_type='application/x-www-form-urlencoded')#THis right now only routes to teh page
    assert response.status_code == 200