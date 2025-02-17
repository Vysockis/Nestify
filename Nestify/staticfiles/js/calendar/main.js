document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded. Initializing FullCalendar...");

    // Ensure FullCalendar is loaded
    if (typeof FullCalendar === 'undefined') {
        console.error("Error: FullCalendar is not loaded! Check script order.");
        return;
    }

    var calendarEl = document.getElementById('calendar');

    if (!calendarEl) {
        console.error("Error: Calendar element not found!");
        return;
    }

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'lt', // Lithuanian language
        events: './api/events/', // Fetch events dynamically
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        eventClick: function(info) {
            console.log("Event clicked! ID:", info.event);
        }
    });

    calendar.render();
});
