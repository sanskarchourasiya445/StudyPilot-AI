from ai_engine.engine import AIEngine

engine = AIEngine()

print("Initializing engine...")
engine.initialize()

print("Health:")
print(engine.health())

print("\nVersion:")
print(engine.version())