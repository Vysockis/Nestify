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
        buttonText: {
            today: 'Šiandien',
            month: 'Mėnesis',
            week: 'Savaitė',
            day: 'Diena'
        },
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            meridiem: false,
            hour12: false
        },
        displayEventTime: true,
        displayEventEnd: true,
        eventDisplay: 'block',
        eventContent: function(arg) {
            let timeText = arg.timeText;
            let title = arg.event.title;
            
            return {
                html: '<div class="fc-event-main-content">' +
                     '<span class="fc-event-time">' + timeText + '</span>' +
                     '<span class="fc-event-title">' + title + '</span>' +
                     '</div>'
            };
        },
        eventClick: function(info) {
            if (info.event.url) {
                window.location.href = info.event.url;
                return false;
            }
        }
    });

    calendar.render();
});
