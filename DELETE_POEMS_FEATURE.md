# Delete Poems Feature

## Overview
Added functionality to delete poems and their associated audio files from the MARTA-Poetry system.

## Backend Changes

### New Endpoint: DELETE /api/narrative/remove-poem/{poem_id}

**Description**: Delete a poem and optionally clean up its associated audio files.

**Request**:
```
DELETE /api/narrative/remove-poem/{poem_id}
```

**Response** (200 OK):
```json
{
  "message": "Successfully removed poem {poem_id}",
  "audio_deleted": 3,
  "audio_missing": 0,
  "audio_errors": []  // optional, only if errors occurred
}
```

**Features**:
- Removes the poem from the graph
- Automatically deletes all audio files referenced in the poem's metadata
- Reports how many audio files were deleted and how many were missing
- Cleans up orphaned entities (themes, imagery, emotions, sound devices) that are no longer used
- Safely handles cases where audio files don't exist on disk

**Location**: [backend/admin_api.py](backend/admin_api.py) - lines 163-198

## Frontend Changes

### UI Components in PoemManager.jsx

#### 1. Single Poem Deletion
- **Location**: Detail panel (right sidebar or mobile drawer)
- **Button**: "Delete Poem" (red button with trash icon style)
- **Behavior**:
  - Shows delete confirmation modal when clicked
  - Modal displays poem title for confirmation
  - Warns that associated audio files will be removed
  - Confirms that action cannot be undone
  - Upon deletion, refreshes poem list and closes detail panel

**Code locations**:
- Delete button: [line 688-691](frontend/src/components/PoemManager.jsx#L688)
- Confirmation modal: [line 698-723](frontend/src/components/PoemManager.jsx#L698)
- Delete function: [line 282-310](frontend/src/components/PoemManager.jsx#L282)

#### 2. Batch Poem Deletion
- **Location**: Batch mode action bar
- **Button**: "Delete" (red button, only shown when poems selected)
- **Behavior**:
  - Only visible when "Batch Select" mode is active
  - Asks for confirmation before proceeding
  - Deletes multiple poems sequentially
  - Reports total deleted, total audio files removed, and any errors
  - Automatically exits batch mode after completion

**Code locations**:
- Delete button in batch actions: [line 866-872](frontend/src/components/PoemManager.jsx#L866)
- Batch delete function: [line 312-362](frontend/src/components/PoemManager.jsx#L312)

### State Management

New state variables added:
```javascript
const [deleting, setDeleting] = useState(false);           // Loading state during deletion
const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);  // Show confirmation modal
```

### API Integration

Uses existing endpoint: `DELETE /api/narrative/remove-poem/{poem_id}`

Response handling:
- Displays alert with deletion summary (audio files removed)
- Handles partial deletions in batch mode with error reporting
- Refreshes poem list after successful deletion
- Gracefully handles network errors

## Usage Examples

### Delete Single Poem via UI
1. Click on a poem to open detail panel
2. Scroll to bottom
3. Click "Delete Poem" button
4. Confirm in modal dialog
5. Poem and associated audio files are removed

### Batch Delete Multiple Poems
1. Click "Batch Select" button
2. Check boxes next to poems to delete
3. Click "Delete" button in batch actions bar
4. Confirm deletion in dialog
5. All selected poems and their audio files are removed

### Delete via API (curl example)
```bash
curl -X DELETE "http://localhost:8000/api/narrative/remove-poem/poem_MARTA_5_20260131_123456"
```

Response:
```json
{
  "message": "Successfully removed poem poem_MARTA_5_20260131_123456",
  "audio_deleted": 2,
  "audio_missing": 0
}
```

## Error Handling

### Graceful Degradation
- If audio files are missing: Reports count but continues with deletion
- If disk operations fail: Reports specific errors while completing deletion
- If poem not found: Returns 404 error
- If API unreachable: Shows user-friendly error message

### User Feedback
- Loading state shown during deletion ("Deleting..." button text)
- Success alerts show how many audio files were removed
- Error alerts provide specific details
- Disabled state prevents double-clicking

## Technical Details

### Audio File Cleanup
- Searches multiple possible audio directory paths
- Handles both absolute and relative file paths
- Safely removes only files explicitly listed in poem metadata
- No cascading deletes of files from other poems

### Graph Cleanup
- Removes all edges connected to the poem
- Optionally removes orphaned entity nodes (themes, imagery, etc.)
- Only removes entities if no other poems reference them
- Saves updated graph to disk

## Testing Checklist

- [x] Delete single poem with audio files
- [x] Delete single poem without audio files
- [x] Batch delete multiple poems
- [x] Confirm modal appears with correct poem title
- [x] Audio files are actually deleted from disk
- [x] Poem list refreshes after deletion
- [x] Missing audio files don't prevent deletion
- [x] Orphaned entities are cleaned up
- [x] Error messages are helpful and specific
