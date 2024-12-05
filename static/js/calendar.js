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
    
    // Initialize with current week start from the template
    let currentWeekStart = new Date(weekStartStr); // Use weekStartStr defined in the template
    console.log("Current Week Start:", currentWeekStart);
    
    /**
     * Adjusts JavaScript's getDay() output to align with Monday as 0.
     * @param {number} day - The day index from getDay() (0 for Sunday, 6 for Saturday).
     * @returns {number} - Adjusted day index (0 for Monday, 6 for Sunday).
     */
    function getAdjustedDayIndex(day) {
        return (day + 6) % 7;
    }
    
    /**
     * Updates the displayed dates for each weekday in the calendar header.
     * @param {Date} weekStartDate - The starting date of the current week.
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
     * @param {Date} weekStartDate - The starting date of the current week.
     */
    function updateTimeslotDataDays(weekStartDate) {
        // Select all timeslot-events elements
        const timeslotEventContainers = document.querySelectorAll('.timeslot-events');
        
        timeslotEventContainers.forEach(container => {
            // Extract the day index from the container's ID
            const [_, timeslotIndex, dayIndex] = container.id.split('-').map(part => parseInt(part));
            
            // Calculate the new date for this day index
            const newDate = new Date(weekStartDate.getTime() + dayIndex * 24 * 60 * 60 * 1000);
            const formattedDate = newDate.toISOString().split('T')[0];
            
            // Update the data-day attribute
            container.setAttribute('data-day', formattedDate);
        });
    }
    
    /**
     * Fetches and renders events for a specific week.
     * @param {Date} weekStartDate - The starting date of the current week.
     */
    function fetchAndRenderEvents(weekStartDate) {
        // Format weekStartDate to YYYY-MM-DD
        const weekStartStrFormatted = weekStartDate.toISOString().split('T')[0];
        console.log("Fetching events for week starting on:", weekStartStrFormatted);
        
        // Update the URL with the new week_start parameter
        history.pushState({}, '', `?week_start=${weekStartStrFormatted}`);
        
        // Fetch events from the server via AJAX
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
     * Renders events on the calendar with proper handling of overlapping events.
     * @param {Array} eventsToRender - Array of event objects to render.
     */
    function renderEvents(eventsToRender) {
        // Clear existing events
        const eventContainers = document.querySelectorAll('.timeslot-events');
        eventContainers.forEach(container => {
            container.innerHTML = '';
        });

        // Create a mapping from container ID to array of events
        const containerEventsMap = {};

        eventsToRender.forEach(event => {
            const eventStart = new Date(event.starttime);
            const eventEnd = new Date(event.endtime);

            const dayIndex = getAdjustedDayIndex(eventStart.getDay());
            const startHour = eventStart.getHours();
            const timeslotIndex = Math.floor(startHour / 2);

            const containerId = `timeslot-${timeslotIndex}-${dayIndex}`;
            if (!containerEventsMap[containerId]) {
                containerEventsMap[containerId] = [];
            }
            containerEventsMap[containerId].push(event);
        });

        // Now, for each container, render its events with overlap handling
        for (const containerId in containerEventsMap) {
            const container = document.getElementById(containerId);
            if (container) {
                const events = containerEventsMap[containerId];
                
                // Sort events by start time
                events.sort((a, b) => new Date(a.starttime) - new Date(b.starttime));

                // Array to keep track of columns and their latest end times
                const columns = [];

                events.forEach(event => {
                    const eventStart = new Date(event.starttime);
                    const eventEnd = new Date(event.endtime);
                
                    let placed = false;
                    for (let i = 0; i < columns.length; i++) {
                        if (eventStart >= columns[i]) {
                            // Place event in this column
                            columns[i] = eventEnd;
                            event.column = i;
                            placed = true;
                            break;
                        }
                    }
                
                    if (!placed) {
                        // Create new column
                        columns.push(eventEnd);
                        event.column = columns.length - 1;
                    }
                });
                
                const totalColumns = columns.length;
                
                events.forEach(event => {
                    const eventDiv = document.createElement('div');
                    eventDiv.classList.add('event');
                    eventDiv.innerText = event.name;

                    // Add click listener to show event details
                    eventDiv.addEventListener('click', (e) => {
                        e.stopPropagation(); // Prevent triggering the container's click event
                        openEventModal(event);
                    });
                
                    const startMinutes = new Date(event.starttime).getMinutes();
                    const durationMs = new Date(event.endtime) - new Date(event.starttime);
                    const durationHours = durationMs / (1000 * 60 * 60);
                
                    // Position within timeslot
                    eventDiv.style.top = `${(startMinutes / 60) * 100}%`;
                    eventDiv.style.height = `${(durationHours / 2) * 100}%`;
                
                    // Horizontal positioning
                    eventDiv.style.width = `${100 / totalColumns}%`;
                    eventDiv.style.left = `${(event.column * 100) / totalColumns}%`;
                
                    container.appendChild(eventDiv);
                });

            } else {
                console.warn(`Container with ID ${containerId} not found for events:`, containerEventsMap[containerId]);
            }
        }
    }

    /**
     * Updates the week range header.
     * @param {Date} weekStartDate - The starting date of the current week.
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
     * @param {Object} event - The event object containing details.
     */
    function openEventModal(event) {
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
     * @param {string} day - The date string in YYYY-MM-DD format.
     * @param {string} time - The time string in HH:MM format.
     */
    function openAddEventModal(day, time) {
        addEventModal.style.display = 'block';
        // Pre-fill the start time based on the clicked timeslot
        const startTimeInput = document.getElementById('start-time');
        const endTimeInput = document.getElementById('end-time');

        const [hour, minute] = time.split(':');
        const startDateTime = new Date(day);
        startDateTime.setHours(parseInt(hour), parseInt(minute));

        // Set start time input
        const formattedStart = startDateTime.toISOString();
        startTimeInput.value = formattedStart;

        // Set end time input (default +2 hours)
        const endDateTime = new Date(startDateTime.getTime() + 2 * 60 * 60 * 1000);
        const formattedEnd = endDateTime.toISOString();
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

    // Add event listener to timeslot-events for adding new events
    const timeslotEventContainers = document.querySelectorAll('.timeslot-events');
    timeslotEventContainers.forEach(container => {
        container.addEventListener('click', (e) => {
            const day = container.getAttribute('data-day');
            const time = container.getAttribute('data-time');
            openAddEventModal(day, time);
        });
    });

    /**
     * Handles the submission of the add event form.
     */
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
