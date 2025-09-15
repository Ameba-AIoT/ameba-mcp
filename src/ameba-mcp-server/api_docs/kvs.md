### KVS Module (Pro2 Only)

AWS Kinesis Video Streams with object detection.

| Function | Description | Returns |
|----------|-------------|---------|
| `kvs_set_objects(objects)` | Set objects to detect | Status with objects list |
| `kvs_reactivate()` | Reactivate with same objects | Reactivation status |
| `kvs_wait_for_start(timeout=180)` | Wait for recording to begin | Recording start status |
| `kvs_wait_for_completion(timeout=60)` | Wait for recording to end | Recording completion status |

<details>
<summary>📘 Detailed Parameters</summary>

#### `kvs_set_objects(objects)`
- **objects** (List[str]): COCO dataset objects - e.g., ["person", "car", "dog"]
- **Note**: Triggers 30-second recording when object detected

#### `kvs_reactivate()`
- No parameters - uses previously set objects
- **Note**: Use after recording completes to re-arm detection

#### `kvs_wait_for_start(timeout=180)`
- **timeout** (float): Maximum seconds to wait - default 180
- **Note**: Returns immediately when recording starts

#### `kvs_wait_for_completion(timeout=60)`
- **timeout** (float): Maximum seconds to wait - default 60
- **Note**: Returns immediately when recording completes

</details>