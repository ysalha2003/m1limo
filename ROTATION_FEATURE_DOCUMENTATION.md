# Next Reservation Rotation Feature

## Overview

When multiple trips are scheduled at the **exact same pickup time**, the Next Reservation card now automatically rotates between them, displaying each trip for 3 seconds before smoothly transitioning to the next.

## Implementation

### Backend Changes (views.py)

Modified dashboard view to pass all trips at the same time:

```python
# Get the next upcoming trip
next_upcoming = Booking.objects.filter(
    status='Confirmed',
    is_return_trip=False
).filter(future_filter).order_by('pick_up_date', 'pick_up_time').first()

# Get ALL trips at the same time as next_upcoming (for rotation display)
next_upcoming_trips = []
if next_upcoming:
    same_time_trips = Booking.objects.filter(
        status='Confirmed',
        is_return_trip=False,
        pick_up_date=next_upcoming.pick_up_date,
        pick_up_time=next_upcoming.pick_up_time
    ).filter(future_filter).order_by('passenger_name')
    next_upcoming_trips = list(same_time_trips)

context['next_upcoming_trip'] = next_upcoming  # First trip (for backward compatibility)
context['next_upcoming_trips'] = next_upcoming_trips  # All trips at same time
```

### Frontend Changes (dashboard.html)

#### 1. Trip Counter Badge

Shows current position (e.g., "1/3", "2/3", "3/3"):

```html
{% if next_upcoming_trips and next_upcoming_trips|length > 1 %}
    <span id="trip-counter" style="...">
        1/{{ next_upcoming_trips|length }}
    </span>
{% endif %}
```

#### 2. Multiple Trip Items

Each trip is rendered in a separate container:

```html
<div id="next-reservation-container" style="position: relative;">
    {% for trip in next_upcoming_trips %}
    <div class="trip-rotation-item" 
         data-trip-index="{{ forloop.counter0 }}"
         data-trip-id="{{ trip.id }}"
         style="opacity: {% if forloop.first %}1{% else %}0{% endif %}; 
                transition: opacity 0.5s ease-in-out;">
        <!-- Trip details: date, time, countdown, location, passenger -->
    </div>
    {% endfor %}
</div>
```

#### 3. Rotation JavaScript

Automatically rotates every 3 seconds with smooth fade transitions:

```javascript
function rotateNextReservationTrips() {
    const tripItems = document.querySelectorAll('.trip-rotation-item');
    if (tripItems.length <= 1) return; // No rotation for single trip
    
    function showTrip(index) {
        // Fade out current trip (0.5s)
        tripItems[currentTripIndex].style.opacity = '0';
        
        // After fade out, hide and show next
        setTimeout(() => {
            tripItems[currentTripIndex].style.display = 'none';
            tripItems[index].style.display = 'flex';
            
            // Fade in next trip
            setTimeout(() => {
                tripItems[index].style.opacity = '1';
            }, 50);
            
            // Update counter badge
            counter.textContent = `${index + 1}/${tripItems.length}`;
            
            // Update click handler for correct booking
            container.onclick = function() {
                window.location.href = `/bookings/${tripId}/`;
            };
        }, 500);
    }
    
    // Rotate every 3 seconds
    setInterval(() => {
        const nextIndex = (currentTripIndex + 1) % tripItems.length;
        showTrip(nextIndex);
    }, 3000);
}
```

#### 4. Multiple Countdown Support

Updated to handle countdowns for all trips (not just one):

```javascript
function updateAllCountdowns() {
    const countdownElements = document.querySelectorAll('.live-countdown');
    
    countdownElements.forEach(countdownElement => {
        // Calculate and update countdown for each trip
        // Uses Chicago timezone consistently
    });
}
```

## User Experience

### Single Trip (No Rotation)
```
┌─────────────────────────────────────────────────┐
│ Next Reservation                           🔵   │
│                                                  │
│ Jan 17, 2026  6:00 AM  PICKUP TIME              │
│ 📍 Wheaton College...  •  👤 Amanda Taylor      │
└─────────────────────────────────────────────────┘
```

### Multiple Trips (With Rotation)
```
┌─────────────────────────────────────────────────┐
│ Next Reservation  [1/2]                    🔵   │
│                                                  │
│ Jan 17, 2026  6:00 AM  PICKUP TIME              │
│ 📍 Wheaton College...  •  👤 Amanda Taylor      │
└─────────────────────────────────────────────────┘
        ⬇ (3 seconds, fade transition)
┌─────────────────────────────────────────────────┐
│ Next Reservation  [2/2]                    🔵   │
│                                                  │
│ Jan 17, 2026  6:00 AM  PICKUP TIME              │
│ 📍 405 Walters Lane  •  👤 Titan Bahan          │
└─────────────────────────────────────────────────┘
        ⬇ (3 seconds, fade transition)
        [Loops back to 1/2]
```

## Features

✅ **Automatic Detection**: Backend automatically finds all trips at the same time
✅ **Smooth Transitions**: 0.5s fade out/in for professional appearance  
✅ **Counter Badge**: Shows current position (e.g., "2/3")
✅ **Click Navigation**: Each trip links to its detail page
✅ **Countdown Updates**: All countdowns update every second
✅ **No Flickering**: Proper timing prevents visual glitches
✅ **Single Trip Fallback**: No rotation when only one trip exists

## Technical Details

### Timing Sequence
1. **0.0s**: Trip A visible (opacity: 1)
2. **3.0s**: Start fade out (opacity: 0) - takes 0.5s
3. **3.5s**: Hide Trip A, show Trip B (display: none/flex)
4. **3.55s**: Start fade in Trip B (opacity: 1) - takes 0.5s
5. **4.0s**: Trip B fully visible
6. **7.0s**: Repeat for Trip C (if exists) or back to Trip A

### Transition CSS
```css
transition: opacity 0.5s ease-in-out;
```

### Why 3 Seconds?
- Long enough to read trip details comfortably
- Short enough to see all trips quickly
- Standard for carousel-style UIs
- Can be adjusted by changing `setInterval(rotateToNext, 3000)`

## Maintenance

### Adjusting Rotation Speed
Change the interval in dashboard.html:
```javascript
// Slower (5 seconds)
tripRotationInterval = setInterval(rotateToNext, 5000);

// Faster (2 seconds)  
tripRotationInterval = setInterval(rotateToNext, 2000);
```

### Adjusting Transition Speed
Change the CSS transition in dashboard.html:
```css
/* Faster fade (0.3s) */
transition: opacity 0.3s ease-in-out;

/* Slower fade (1s) */
transition: opacity 1s ease-in-out;
```

### Testing
Create test bookings at the same time:
```python
from models import Booking
from datetime import date, time

# Create 3 trips at 10:00 AM tomorrow
tomorrow = date.today() + timedelta(days=1)
pickup_time = time(10, 0)

for passenger in ['Alice', 'Bob', 'Charlie']:
    Booking.objects.create(
        user=user,
        passenger_name=passenger,
        pick_up_date=tomorrow,
        pick_up_time=pickup_time,
        status='Confirmed',
        # ... other fields
    )
```

## Edge Cases Handled

1. **Single trip**: No rotation, no counter badge
2. **Multiple trips**: Full rotation with counter
3. **No trips**: Shows "No upcoming reservations"
4. **Return trips**: Excluded to avoid duplicates
5. **Different times**: Only groups exact time matches
6. **Countdown accuracy**: Each trip has independent countdown
7. **Click behavior**: Correct booking detail page for each trip

---

**Date Implemented**: January 17, 2026  
**Feature**: Next Reservation Rotation for Same-Time Trips  
**Status**: ✅ Ready for production
