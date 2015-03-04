#!env/bin/python
from csgocal import CSGOCalendar

def main():
    calendar = CSGOCalendar()
    calendar.updateESEAInfo()

if __name__ == "__main__":
    main()
