# Registration service
from users.v2.services.registration_service import RegistrationService

# SendEvent service
from users.v2.services.send_events_service import SendEventsService

all = [
    RegistrationService,
    SendEventsService,
]
