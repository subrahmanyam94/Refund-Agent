from datetime import date, datetime
import logging
from uuid import uuid4
from data import users_data
from dotenv import load_dotenv
from langchain.tools import tool
from objects import PurchaseItem

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s "
)

@tool
def get_user_purchase_history(user: str) -> dict:
    """Retrieves the customer order purchase history given their username."""
    logging.info(f"using get_user_purchase_history tool on user: {user}")
    if users_data.get(user):
        return {"found": True, "username": user, "orders": users_data[user]}
    return {
        "found": False,
        "status": "USERNAME_NOT_FOUND",
        "username": user,
        "message": f"No account found with username '{user}'. Stop all tool calls. Ask the user to provide the correct username."
    }






@tool
def calculate_right_refund(user: str, items: list[PurchaseItem]) -> dict:
    """Calculates refund eligibility and amount for the requested items.
    Internally retrieves today's date, checks if each purchase is within the 30-day window
    and not in the future, and returns purchase date, today's date, days elapsed, and eligibility.
    """
    logging.info(f"using calculate_right_refund tool to get user: {user} refund for items: {items}")
    if not users_data.get(user):
        return {
            "found": False,
            "status": "USERNAME_NOT_FOUND",
            "username": user,
            "message": f"No account found with username '{user}'. Do NOT call issue_refund_ticket. Ask the user for a correct username.",
            "eligible": False,
            "refund_amount": 0
        }

    today = date.today()
    today_str = today.isoformat()
    user_orders = users_data[user]

    total_refund = 0.0
    purchase_dates = []
    days_elapsed = []
    eligible_items = []
    ineligible_items = []

    for item in items:
        item_name = item.name
        if item_name in user_orders:
            order_info = user_orders[item_name]
            p_date_raw = order_info["date"]
            try:
                p_date = datetime.strptime(p_date_raw, "%Y-%m-%d").date()
            except ValueError:
                # Fallback: manual split for non-zero-padded dates like "2026-9-5"
                parts = [int(p) for p in p_date_raw.split("-")]
                p_date = date(parts[0], parts[1], parts[2])

            p_date_str = p_date.isoformat()
            purchase_dates.append(p_date_str)
            days = (today - p_date).days
            days_elapsed.append(days)

            # Within 30 days and not in the future
            if 0 <= days <= 30:
                total_refund += float(order_info["price"])
                eligible_items.append({
                    "name": item_name,
                    "price": float(order_info["price"]),
                    "purchase_date": p_date_str,
                    "days_since_purchase": days
                })
            else:
                ineligible_items.append({
                    "name": item_name,
                    "price": float(order_info["price"]),
                    "purchase_date": p_date_str,
                    "days_since_purchase": days,
                    "reason": "outside 30-day refund window" if days > 30 else "future purchase date"
                })
        else:
            ineligible_items.append({
                "name": item_name,
                "reason": "item not found in purchase history"
            })

    is_eligible = len(eligible_items) > 0
    p_dates_str = ", ".join(purchase_dates) if purchase_dates else "N/A"
    primary_days = days_elapsed[0] if days_elapsed else 0
    all_days_elapsed = dict(zip(purchase_dates, days_elapsed))

    return {
        "purchase_date": p_dates_str,
        "today_date": today_str,
        "days_since_purchase": primary_days,
        "days_per_item": all_days_elapsed,
        "within_30_day_window": is_eligible,
        "refund_amount": int(round(total_refund)),
        "eligible": is_eligible,
        "eligible_items": eligible_items,
        "ineligible_items": ineligible_items
    }

@tool
def issue_refund_ticket(user: str, refund_amount: float) -> dict:
    """Issues a refund ticket with a unique ticket ID for the customer.
    ONLY call this tool if calculate_right_refund returned eligible=True AND refund_amount > 0.
    Do NOT call this tool if refund_amount is 0 or the customer is not eligible.
    Do NOT call this tool more than once.

    Args:
        user: The customer username.
        refund_amount: The total refund amount in dollars (e.g. 7.0). Must be > 0. Pass the exact value from calculate_right_refund.
    """
    logging.info(f"using issue_refund_ticket for user: {user}, amount: {refund_amount}")

    # Hard guard — reject zero or negative amounts
    if refund_amount <= 0:
        logging.warning(f"issue_refund_ticket called with invalid amount {refund_amount} for user {user}. Rejecting.")
        return {
            "status": "error",
            "ticket_id": None,
            "user": user,
            "refund_amount": 0,
            "message": "Refund ticket was NOT issued because the refund amount is 0 or the customer is not eligible. Do not retry."
        }

    ticket_id = f"REF-{user}-{uuid4().hex[:6].upper()}"
    rounded_amount = int(round(refund_amount))
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "user": user,
        "refund_amount": rounded_amount,
        "message": f"A refund ticket {ticket_id} has been issued successfully for ${rounded_amount}. Do NOT call this tool again."
    }

# --- Quick test ---
#result = issue_refund_ticket.invoke({"user": "user123", "refund_amount": 7.0})
#print(result)

