# _DIR_META.md

## Architecture Vision (Max 3 lines)
The bedrock of the application. Contains configuration schemas and quota limiters.
Strictly isolated from business logic.

## Member Index
- `_DIR_META.md`: [Meta] **Update me if structure changes.**
- `config.py`: [Config] JSON Config storage and retrieval.
- `quota.py`: [Limiter] Quota usage tracking.

> ⚠️ **Protocol**: Sync this file whenever directory content or responsibility shifts.
