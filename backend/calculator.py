"""
Calculator utility for appointment time slots, department capacity,
and consultation fee calculations.
"""
from datetime import datetime, timedelta

def parse_time(time_str):
    """Parse HH:MM string into datetime.time object."""
    try:
        return datetime.strptime(time_str.strip(), "%H:%M").time()
    except Exception:
        return None

def generate_slots(start_time_str="09:00", end_time_str="17:00", interval_minutes=30):
    """
    Generate slot list between start and end time.
    E.g. ['09:00', '09:30', '10:00', ...]
    """
    slots = []
    try:
        current = datetime.strptime(start_time_str.strip(), "%H:%M")
        end = datetime.strptime(end_time_str.strip(), "%H:%M")
        while current + timedelta(minutes=interval_minutes) <= end:
            slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=interval_minutes)
    except Exception:
        # Default fallback standard slots
        return ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
                "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
    return slots

def is_day_available(target_date_str, available_days_str):
    """
    Check if a YYYY-MM-DD date corresponds to an available day of the week.
    e.g. available_days_str = "Monday, Tuesday, Wednesday, Friday"
    """
    if not available_days_str or "all" in available_days_str.lower() or "daily" in available_days_str.lower():
        return True
    try:
        date_obj = datetime.strptime(target_date_str.strip(), "%Y-%m-%d")
        day_name = date_obj.strftime("%A")  # e.g. "Monday"
        allowed_days = [d.strip().lower() for d in available_days_str.split(",")]
        return day_name.lower() in allowed_days
    except Exception:
        return True

def calculate_consultation_total(base_fee, tax_rate=0.05, discount=0.0):
    """
    Calculate total consultation charges with tax and any applicable discount.
    """
    fee = float(base_fee)
    discount_amount = fee * (discount / 100.0)
    taxable = fee - discount_amount
    tax = taxable * tax_rate
    total = taxable + tax
    return {
        "base_fee": round(fee, 2),
        "discount": round(discount_amount, 2),
        "tax": round(tax, 2),
        "total": round(total, 2)
    }

def estimate_wait_time(booked_slots_count, avg_duration_minutes=20):
    """
    Estimate patient wait time based on the number of appointments ahead.
    """
    minutes = booked_slots_count * avg_duration_minutes
    return {
        "estimated_wait_minutes": minutes,
        "queue_position": booked_slots_count + 1
    }
