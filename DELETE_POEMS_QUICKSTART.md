# Quick Start: Delete Poems Feature

## What's New

Users can now delete poems and their associated audio files from the MARTA-Poetry system through the Poem Manager UI.

## How to Use

### Delete a Single Poem

1. Open the **Poem Manager** tab in the Admin Panel
2. Click on any poem in the list to view its details
3. In the detail panel (right side or bottom drawer on mobile), click the **Delete Poem** button
4. A confirmation dialog will appear showing:
   - The poem's title
   - Warning that audio files will be removed
   - Warning that this action cannot be undone
5. Click **Delete** to confirm or **Cancel** to abort
6. The poem and all its audio files are removed
7. The poem list automatically refreshes

### Delete Multiple Poems (Batch Mode)

1. Open the **Poem Manager** tab
2. Click the **Batch Select** button in the filters section
3. Checkboxes will appear next to each poem
4. Select the poems you want to delete by checking their boxes
5. In the batch actions bar, you'll see:
   - Number of poems selected
   - Three action buttons: "Mark as Core", "Mark as Extension", and **"Delete"**
6. Click the **Delete** button
7. Confirm the action in the dialog
8. All selected poems and their audio files are removed
9. The list refreshes and batch mode is automatically closed

## What Gets Deleted

✅ The poem record from the database/graph  
✅ All audio files associated with the poem  
✅ All metadata linked to the poem  
✅ Orphaned themes, imagery, emotions, and sound devices that are no longer used  

❌ Other poems (even if related)  
❌ Poetry graph relationships (unless orphaned)  
❌ Any other system data  

## Feedback You'll See

After deletion, you'll see an alert message like:
- ✅ **Success**: "Deleted poem. Audio files removed: 3"
- ⚠️ **Partial Success**: "Deleted poem. Audio files removed: 2 (1 files not found)"
- ❌ **Error**: "Failed to delete poem: [reason]"

## Batch Deletion Status

When deleting multiple poems:
- You'll see: "Deleted X of Y poems. Audio files removed: Z"
- If any poems failed: Error details are shown
- Successful deletions still persist even if some fail

## API Endpoint (For Developers)

```bash
DELETE /api/narrative/remove-poem/{poem_id}
```

Example:
```bash
curl -X DELETE "http://localhost:8000/api/narrative/remove-poem/poem_MARTA_5_20260131_120000"
```

Response:
```json
{
  "message": "Successfully removed poem poem_MARTA_5_20260131_120000",
  "audio_deleted": 3,
  "audio_missing": 0
}
```

## Safety Features

- ✅ Confirmation required before deletion
- ✅ Clear warnings about what will be deleted
- ✅ Ability to cancel at the confirmation screen
- ✅ Disabled buttons prevent accidental double-clicks
- ✅ Loading state shows "Deleting..." while processing
- ✅ Missing files don't break the deletion process
- ✅ All errors are reported to the user

## Technical Implementation

**Files Modified**:
- Backend: `backend/admin_api.py` (delete endpoint logic)
- Frontend: `frontend/src/components/PoemManager.jsx` (UI & state management)

**New Endpoint**: `DELETE /api/narrative/remove-poem/{poem_id}`

**Capabilities**:
- Single poem deletion with confirmation
- Batch deletion of multiple poems
- Automatic audio file cleanup
- Orphaned entity removal
- Comprehensive error reporting

For technical details, see [DELETE_POEMS_FEATURE.md](DELETE_POEMS_FEATURE.md).
