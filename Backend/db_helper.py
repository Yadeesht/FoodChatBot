import mysql.connector
global cnx
from passw import dbpass

cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password=dbpass,
    database="pandeyji_eatery"
)

def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        cnx.commit()

        cursor.close()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        cnx.rollback()

        return -1

    except Exception as e:
        print(f"An error occurred: {e}")
        
        cnx.rollback()

        return -1
    
def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()

    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))
    cnx.commit()
    cursor.close()

def get_total_order_price(order_id: int):
    cursor = cnx.cursor()
    query = f"select get_total_order_price({order_id})"
    cursor.execute(query)   
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result[0] is not None else 0

def get_order_id():
    cursor = cnx.cursor();
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    
    return int(result[0]) + 1 if result[0] is not None else 1

def get_order_status(order_id: int):
    cursor = cnx.cursor()

    query = ("select status from order_tracking where order_id=%s")
    cursor.execute(query,(order_id,))

    result = cursor.fetchone()
    cnx.commit() 
    cursor.close()

    if result is not None:
        return result[0]
    else:
        return None
    
def get_str_from_food_dict(food_dict: dict):
    return ", ".join([f"{int(quantity)} {food_item}" for food_item, quantity in food_dict.items()])










