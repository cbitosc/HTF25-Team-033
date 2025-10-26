"""
Patch ChromaDB telemetry to prevent annoying warnings
"""
import logging
import os

# Set environment variable before any ChromaDB imports
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

# Disable ChromaDB logging
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('chromadb.telemetry').setLevel(logging.ERROR)

def patch_chromadb_telemetry():
    """Completely disable ChromaDB telemetry"""
    try:
        # Try to patch the telemetry module
        import chromadb.telemetry.posthog as posthog_module
        
        # Create a dummy capture function that does nothing
        def dummy_capture(*args, **kwargs):
            pass
        
        # Replace the capture method
        if hasattr(posthog_module, 'Posthog'):
            posthog_module.Posthog.capture = dummy_capture
            print("✓ ChromaDB telemetry disabled")
        
    except ImportError:
        # If the module structure is different, try alternative approaches
        try:
            import chromadb.telemetry as telemetry
            
            # Monkey-patch the entire telemetry system
            class DummyTelemetry:
                def capture(self, *args, **kwargs):
                    pass
                
                def __call__(self, *args, **kwargs):
                    pass
            
            if hasattr(telemetry, 'posthog'):
                telemetry.posthog.Posthog = DummyTelemetry
                print("✓ ChromaDB telemetry disabled (alternative method)")
                
        except Exception as e:
            print(f"Could not patch telemetry: {e}")
    
    except Exception as e:
        print(f"Could not patch telemetry: {e}")

# Apply patch immediately when imported
patch_chromadb_telemetry()