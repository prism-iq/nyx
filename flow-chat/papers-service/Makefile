.PHONY: build run deploy clean

BINARY=papers-service
PORT=8200

build:
	cd cmd && go build -o ../$(BINARY) .

run: build
	./$(BINARY)

deploy: build
	sudo cp $(BINARY) /usr/local/bin/
	sudo cp papers-service.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable papers-service
	sudo systemctl restart papers-service
	@echo "◯ papers-service deployed on :$(PORT)"

status:
	@curl -s http://localhost:$(PORT)/health | jq .

logs:
	journalctl -u papers-service -f

clean:
	rm -f $(BINARY)

# Dev mode with hot reload
dev:
	@which air > /dev/null || go install github.com/cosmtrek/air@latest
	air -c .air.toml

# Test endpoints
test-health:
	curl -s http://localhost:$(PORT)/health | jq .

test-submit:
	curl -X POST http://localhost:$(PORT)/api/submit \
		-H "Content-Type: application/json" \
		-d '{"cid":"QmTest123","tier":50}' | jq .
