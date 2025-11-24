from guardrails import install

try:
    from guardrails.hub import DetectPII
except ImportError:
    install("hub://guardrails/detect_pii", False)