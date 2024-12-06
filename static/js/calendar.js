document.addEventListener('DOMContentLoaded', () => {
    const prevWeekBtn = document.getElementById('prev-week');
    const nextWeekBtn = document.getElementById('next-week');
    const weekRangeHeader = document.getElementById('week-range');
    const eventModal = document.getElementById('event-modal');
    const addEventModal = document.getElementById('add-event-modal');
    const closeButtons = document.querySelectorAll('.close-button');
    const modalEventName = document.getElementById('modal-event-name');
    const modalEventTime = document.getElementById('modal-event-time');
    const modalEventLocation = document.getElementById('modal-event-location');
    const addEventForm = document.getElementById('add-event-form');
    const deleteEventButton = document.getElementById('delete-event-button');
    const deleteEventError = document.getElementById('delete-event-error');
    
    // Initialize with current week start from the template
    let currentWeekStart = new Date(weekStartStr); // Use weekStartStr defined in the template
    console.log("Current Week Start:", currentWeekStart);
    let currentEvent = null;

    // Define slot parameters
    const SLOT_DURATION_HOURS = 2; // Each slot is 2 hours
    const FIRST_SLOT_START_HOUR = 0; // Adjusted to 0 (midnight) if needed
    const TOTAL_SLOTS_PER_DAY = 12; // 24 / 2

    /**
     * Adjusts JavaScript's getDay() output to align with Monday as 0.
     * @param {number} day
     * @returns {number}
     */
    function getAdjustedDayIndex(day) {
        return (day + 6) % 7;
    }
    
    /**
     * Updates the displayed dates for each weekday in the calendar header.
     * @param {Date} weekStartDate
     */
    function updateWeekdaysDates(weekStartDate) {
        // Select all weekday-date elements, skipping the first one which is for 'Time'
        const weekdays = document.querySelectorAll('.calendar-weekdays .weekday');
        
        // Iterate over the 7 weekdays
        for (let i = 1; i <= 7; i++) { // Start at 1 to skip the 'Time' column
            const dayDateElement = weekdays[i].querySelector('.weekday-date');
            const currentDay = new Date(weekStartDate.getTime() + (i - 1) * 24 * 60 * 60 * 1000);
            const formattedDate = currentDay.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            dayDateElement.innerText = formattedDate;
        }
    }
    
    /**
     * Updates the data-day attributes for all timeslot-events based on the current week.
     * @param {Date} weekStartDate
     */
    function updateTimeslotDataDays(weekStartDate) {
        // Select all timeslot-events elements
        const timeslotEventContainers = document.querySelectorAll('.timeslot-events');
        
        timeslotEventContainers.forEach(container => {
            // Extract the day index from the container's ID
            const [_, slotIndex, dayIndex] = container.id.split('-').map(part => parseInt(part));
            
            // Calculate the new date for this day index
            const newDate = new Date(weekStartDate.getTime() + dayIndex * 24 * 60 * 60 * 1000);
            const formattedDate = newDate.toISOString().split('T')[0];
            
            // Update the data-day attribute
            container.setAttribute('data-day', formattedDate);
        });
    }
    
    /**
     * Fetches and renders events for a specific week.
     * @param {Date} weekStartDate
     */
    function fetchAndRenderEvents(weekStartDate) {
        // Format weekStartDate to YYYY-MM-DD
        const weekStartStrFormatted = weekStartDate.toISOString().split('T')[0];
        console.log("Fetching events for week starting on:", weekStartStrFormatted);
        
        // Update the URL with the new week_start parameter
        history.pushState({}, '', `?week_start=${weekStartStrFormatted}`);
        
        fetch(`/get_events?week_start=${weekStartStrFormatted}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    console.error("Error fetching events:", data.error);
                    return;
                }
                console.log("Fetched Events:", data.events);
                const filteredEvents = data.events;
                renderEvents(filteredEvents);
                updateWeekRangeHeader(weekStartDate);    // Update week range header
                updateWeekdaysDates(weekStartDate);      // Update weekdays' dates
                updateTimeslotDataDays(weekStartDate);   // Update data-day attributes
            })
            .catch(error => {
                console.error('Error fetching events:', error);
                alert('An error occurred while fetching events.');
            });
    }

    /**
     * Renders events on the calendar by iterating through relevant timeslot containers.
     * @param {Array} eventsToRender - Array of event objects.
     */
    function renderEvents(eventsToRender) {
        // Clear existing events
        const eventContainers = document.querySelectorAll('.timeslot-events');
        eventContainers.forEach(container => {
            container.innerHTML = '';
        });

        eventsToRender.forEach(event => {
            const eventStart = new Date(event.starttime);
            const eventEnd = new Date(event.endtime);

            const dayIndex = getAdjustedDayIndex(eventStart.getDay()); // 0 for Monday

            // Calculate event start and end times in minutes since midnight
            const startMinutes = eventStart.getHours() * 60 + eventStart.getMinutes();
            const endMinutes = eventEnd.getHours() * 60 + eventEnd.getMinutes();

            console.log(`\nEvent: ${event.name}`);
            console.log(`Start Time: ${eventStart.toLocaleTimeString()}`);
            console.log(`End Time: ${eventEnd.toLocaleTimeString()}`);
            console.log(`Start Minutes: ${startMinutes}`);
            console.log(`End Minutes: ${endMinutes}`);

            // Validate event timing within 24-hour bounds
            if (startMinutes < 0 || endMinutes > 1440 || startMinutes >= endMinutes) {
                console.warn(`Event "${event.name}" has invalid timing and will be skipped.`);
                return;
            }

            // Calculate the starting and ending slot indices
            const startSlotIndex = Math.floor((startMinutes - FIRST_SLOT_START_HOUR * 60) / (SLOT_DURATION_HOURS * 60));
            const endSlotIndex = Math.ceil((endMinutes - FIRST_SLOT_START_HOUR * 60) / (SLOT_DURATION_HOURS * 60));

            // Ensure slot indices are within valid range
            const adjustedStartSlotIndex = Math.max(0, startSlotIndex);
            const adjustedEndSlotIndex = Math.min(TOTAL_SLOTS_PER_DAY, endSlotIndex);

            console.log(`Start Slot Index: ${adjustedStartSlotIndex}`);
            console.log(`End Slot Index: ${adjustedEndSlotIndex}`);

            // Iterate through each timeslot the event spans
            for (let slotIndex = adjustedStartSlotIndex; slotIndex < adjustedEndSlotIndex; slotIndex++) {
                const containerId = `timeslot-${slotIndex}-${dayIndex}`;
                const container = document.getElementById(containerId);

                if (container) {
                    if (slotIndex === adjustedStartSlotIndex) {
                        // First timeslot: create the main event box
                        const slotStartTime = FIRST_SLOT_START_HOUR * 60 + slotIndex * SLOT_DURATION_HOURS * 60;
                        const slotEndTime = slotStartTime + SLOT_DURATION_HOURS * 60;

                        // Calculate the overlap within this slot
                        const overlapStart = Math.max(startMinutes, slotStartTime);
                        const overlapEnd = Math.min(endMinutes, slotEndTime);
                        const overlapDuration = overlapEnd - overlapStart;
                        const overlapPercentage = (overlapDuration / (SLOT_DURATION_HOURS * 60)) * 100;

                        // Define the minimum overlap percentage required to display the event name
                        const MIN_OVERLAP_PERCENTAGE = 50; // Display name only if event box is >= 50% of cell

                        // Create the main event div
                        const eventDiv = document.createElement('div');
                        eventDiv.classList.add('event');

                        // Conditionally set the event name based on overlap percentage
                        if (overlapPercentage >= MIN_OVERLAP_PERCENTAGE) {
                            eventDiv.innerText = event.name;
                        } else {
                            eventDiv.innerText = ''; // Do not display the event name
                        }

                        eventDiv.style.top = `${((overlapStart - slotStartTime) / (SLOT_DURATION_HOURS * 60)) * 100}%`;
                        eventDiv.style.height = `${overlapPercentage}%`;

                        // Add click listener to show event details
                        eventDiv.addEventListener('click', (e) => {
                            e.stopPropagation(); // Prevent triggering the container's click event
                            openEventModal(event);
                        });

                        // Style the event box
                        eventDiv.style.position = 'absolute';
                        eventDiv.style.left = '0';
                        eventDiv.style.width = '100%';

                        // Append the event box to the container
                        container.appendChild(eventDiv);
                    } else if (slotIndex === adjustedEndSlotIndex - 1) {
                        // Last timeslot: create a partial continuation marker
                        const slotStartTime = FIRST_SLOT_START_HOUR * 60 + slotIndex * SLOT_DURATION_HOURS * 60;
                        const slotEndTime = slotStartTime + SLOT_DURATION_HOURS * 60;

                        const overlapStart = Math.max(startMinutes, slotStartTime);
                        const overlapEnd = Math.min(endMinutes, slotEndTime);
                        const overlapDuration = overlapEnd - overlapStart;
                        const overlapPercentage = (overlapDuration / (SLOT_DURATION_HOURS * 60)) * 100;

                        // Create the continuation marker
                        const continuationDiv = document.createElement('div');
                        continuationDiv.classList.add('event-continuation');
                        continuationDiv.style.height = `${overlapPercentage}%`;
                        continuationDiv.style.top = '0%';
                        continuationDiv.style.width = '100%';

                        container.appendChild(continuationDiv);
                    } else {
                        // Middle timeslots: create full-height continuation markers
                        const continuationDiv = document.createElement('div');
                        continuationDiv.classList.add('event-continuation');
                        continuationDiv.style.height = `100%`;
                        continuationDiv.style.top = '0%';
                        continuationDiv.style.width = '100%';

                        container.appendChild(continuationDiv);
                    }
                } else {
                    console.warn(`Container with ID ${containerId} not found for event:`, event);
                }
            }
        });
    }

    /**
     * Updates the week range header.
     * @param {Date} weekStartDate
     */
    function updateWeekRangeHeader(weekStartDate) {
        const weekEndDate = new Date(weekStartDate.getTime() + 6 * 24 * 60 * 60 * 1000);
        const options = { month: 'short', day: 'numeric' };
        const weekRange = `${weekStartDate.toLocaleDateString(undefined, options)} to ${weekEndDate.toLocaleDateString(undefined, options)}`;
        console.log("Week Range:", weekRange);
        weekRangeHeader.innerText = weekRange;
    }

    // Event listeners for navigation buttons
    prevWeekBtn.addEventListener('click', () => {
        currentWeekStart.setDate(currentWeekStart.getDate() - 7);
        fetchAndRenderEvents(currentWeekStart);
    });

    nextWeekBtn.addEventListener('click', () => {
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        fetchAndRenderEvents(currentWeekStart);
    });

    // Handle browser navigation (back/forward buttons)
    window.addEventListener('popstate', () => {
        const urlParams = new URLSearchParams(window.location.search);
        const weekStartStr = urlParams.get('week_start');
        if (weekStartStr) {
            currentWeekStart = new Date(weekStartStr);
            fetchAndRenderEvents(currentWeekStart);
        }
    });

    // Initialize the calendar on page load
    fetchAndRenderEvents(currentWeekStart);

    /**
     * Opens the event details modal with formatted time.
     * @param {Object} event
     */
    function openEventModal(event) {
        // Reset the modal state
        deleteEventError.style.display = 'none';
        currentEvent = null; // Clear any previously selected event

        // Populate the modal with the new event details
        currentEvent = event;
        modalEventName.innerText = `Name: ${event.name}`;
        
        const eventStart = new Date(event.starttime);
        const eventEnd = new Date(event.endtime);
        
        // Define options for formatting date and time
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            hour: 'numeric', 
            minute: 'numeric',
            hour12: true
        };
        
        const formattedStart = eventStart.toLocaleString(undefined, options);
        const formattedEnd = eventEnd.toLocaleString(undefined, options);
        
        modalEventTime.innerText = `Time: ${formattedStart} - ${formattedEnd}`;
        modalEventLocation.innerText = `Location: ${event.location}`;
        eventModal.style.display = 'block';
    }


    /**
     * Opens the add event modal with pre-filled date and time.
     * @param {string} day
     * @param {string} time
     */
    function openAddEventModal(day, time) {
        addEventModal.style.display = 'block';
        // Pre-fill the start time based on the clicked timeslot
        const startTimeInput = document.getElementById('start-time');
        const endTimeInput = document.getElementById('end-time');
    
        const [hour, minute] = time.split(':');
        const startDateTime = new Date(day);
        
        // Manually add +1 day to correct the autofill issue
        startDateTime.setDate(startDateTime.getDate() + 1);
        startDateTime.setHours(parseInt(hour), parseInt(minute));
    
        // Set start time input in "YYYY-MM-DDTHH:MM" format
        const formattedStart = startDateTime.toISOString().slice(0,16); // "YYYY-MM-DDTHH:MM"
        startTimeInput.value = formattedStart;
    
        // Set end time input (default +2 hours)
        const endDateTime = new Date(startDateTime.getTime() + 2 * 60 * 60 * 1000);
        const formattedEnd = endDateTime.toISOString().slice(0,16); // "YYYY-MM-DDTHH:MM"
        endTimeInput.value = formattedEnd;
    }

    // Event listeners for closing modals
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            button.parentElement.parentElement.style.display = 'none';
        });
    });

    // Close modals when clicking outside the modal content
    window.addEventListener('click', (e) => {
        if (e.target == eventModal) {
            eventModal.style.display = 'none';
        }
        if (e.target == addEventModal) {
            addEventModal.style.display = 'none';
        }
    });

    deleteEventButton.addEventListener('click', () => {
        if (!currentEvent) {
            console.error('No event selected for deletion.');
            return;
        }
    
        console.log('Deleting event:', currentEvent);
    
        fetch('/delete_event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ event_name: currentEvent.name }),
        })
            .then(response => {
                console.log('Delete event response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Delete event response data:', data);
                if (data.error) {
                    if (data.error === 'Permission Denied') {
                        deleteEventError.style.display = 'block';
                    } else {
                        alert(`Error: ${data.error}`);
                    }
                } else {
                    alert(`Success: ${data.message}`);
                    eventModal.style.display = 'none';
                    fetchAndRenderEvents(currentWeekStart); // Reload events after successful deletion
                }
            })
            .catch(error => {
                console.error('Error deleting event:', error);
                alert('An error occurred while deleting the event.');
            });
    });


    // Add event listener to timeslot-events for adding new events
    const timeslotEventContainers = document.querySelectorAll('.timeslot-events');
    timeslotEventContainers.forEach(container => {
        container.addEventListener('click', (e) => {
            const day = container.getAttribute('data-day');
            const time = container.getAttribute('data-time');
            openAddEventModal(day, time);
        });
    });


    addEventForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const eventName = document.getElementById('event-name').value.trim();
        const startTime = document.getElementById('start-time').value;
        const endTime = document.getElementById('end-time').value;
        const location = document.getElementById('location').value.trim();

        if (!eventName || !startTime || !endTime || !location) {
            alert('All fields are required.');
            return;
        }

        // Send the event data to the server via POST request
        fetch('/event_setting', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event_name: eventName,
                start_time: startTime,
                end_time: endTime,
                location: location
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                addEventModal.style.display = 'none';
                // Reload events
                fetchAndRenderEvents(currentWeekStart);
            } else if (data.error) {
                alert(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding the event.');
        });
    });
});
