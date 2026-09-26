# Pipeline Configuration Variables
VENUE_CSV    ?= venues.csv
HTML_TEMPLATE ?= venues.html
OUT_HTML     ?= venues.html

.PHONY: all events venues

# Run both operations simultaneously
all: venues

venues:
	python3 build_venues.py $(VENUE_CSV) $(HTML_TEMPLATE) $(OUT_HTML) --var venuesData