from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper

app = FastAPI()

inprogress_orders = {}


@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = output_contexts[0]["name"].split('/')[-3]

    intent_handler_dict = {
        'order.add - ongoing': add_to_order,
        'order.remove - ongoing': remove_from_order,
        'order.complete - ongoing': complete_order,
        'track.order - ongoing': track_order
    }

    return intent_handler_dict[intent](parameters, session_id)

def remove_from_order(parameters: dict, session_id: str):

    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?",
        })
    current_order = inprogress_orders[session_id]
    food_item= parameters['food-item']

    removed_items =[]
    no_such_items = []
    for item in food_item:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]
    
    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = db_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
        

def track_order(parameters: dict, session_id: str):
    order_id = parameters['number']  # number is nothing but the order id
    order_status = db_helper.get_order_status(order_id)
    if order_status:
        fullfillmentText = f"The order status for the order id: {int(order_id)} is: {order_status}"
    else:
        fullfillmentText = f"No order found with order id: {int(order_id)}"
    return JSONResponse(content={
        "fulfillmentText": fullfillmentText,
    })


def add_to_order(parameters: dict, session_id: str):
    food_item = parameters['food-item']
    quantity = parameters["number"]

    if len(food_item)!=len(quantity):
        return JSONResponse(content={
            "fulfillmentText": "The number of food items and quantities do not match. Please try again.",
        })
    else:
        food_dict = dict(zip(food_item, quantity))
        if session_id in inprogress_orders:
            inprogress_orders[session_id].update(food_dict)
        else:       
            inprogress_orders[session_id] = food_dict
        
        order_str = db_helper.get_str_from_food_dict(inprogress_orders[session_id])
        text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": text
    })

def complete_order(parameters: dict, session_id:str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)

            fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"

        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def save_to_db(order: dict):
    order_id = db_helper.get_order_id()
    for food_item, quantity in order.items():
        r = db_helper.insert_order_item(food_item,quantity,order_id)

        if r==-1:
            return -1
            
    db_helper.insert_order_tracking(order_id, "in progress")

    return order_id

