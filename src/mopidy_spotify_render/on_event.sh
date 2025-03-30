#!/bin/bash

# Define JSON file path
EVENT_FILE="/tmp/librespot_event.json"

# Convert COVERS into a JSON array (splitting by newlines)
COVERS_JSON=$(echo "$COVERS" | jq -R -s 'split("\n")')
ALBUM_ARTISTS_JSON=$(echo "$ALBUM_ARTISTS" | jq -R -s 'split("\n")')
ARTISTS_JSON=$(echo "$ARTISTS" | jq -R -s 'split("\n")')

# Create JSON and write to file
jq -n \
  --arg player_event "$PLAYER_EVENT" \
  --arg user_name "$USER_NAME" \
  --arg connection_id "$CONNECTION_ID" \
  --arg client_id "$CLIENT_ID" \
  --arg client_name "$CLIENT_NAME" \
  --arg client_brand_name "$CLIENT_BRAND_NAME" \
  --arg client_model_name "$CLIENT_MODEL_NAME" \
  --arg shuffle "$SHUFFLE" \
  --arg repeat "$REPEAT" \
  --arg auto_play "$AUTO_PLAY" \
  --arg filter "$FILTER" \
  --arg volume "$VOLUME" \
  --arg track_id "$TRACK_ID" \
  --arg position_ms "$POSITION_MS" \
  --arg item_type "$ITEM_TYPE" \
  --arg uri "$URI" \
  --arg name "$NAME" \
  --arg duration_ms "$DURATION_MS" \
  --arg is_explicit "$IS_EXPLICIT" \
  --arg language "$LANGUAGE" \
  --argjson covers "$COVERS_JSON" \
  --arg number "$NUMBER" \
  --arg disc_number "$DISC_NUMBER" \
  --arg popularity "$POPULARITY" \
  --arg album "$ALBUM" \
  --argjson artists "$ARTISTS_JSON" \
  --argjson album_artists "$ALBUM_ARTISTS_JSON" \
  --arg show_name "$SHOW_NAME" \
  --arg description "$DESCRIPTION" \
  --arg format "$FORMAT" \
  '{
    "player_event": $player_event,
    "user_name": $user_name,
    "connection_id": $connection_id,
    "client_id": $client_id,
    "client_name": $client_name,
    "client_brand_name": $client_brand_name,
    "client_model_name": $client_model_name,
    "shuffle": $shuffle,
    "repeat": $repeat,
    "auto_play": $auto_play,
    "filter": $filter,
    "volume": $volume,
    "track_id": $track_id,
    "position_ms": $position_ms,
    "item_type": $item_type,
    "uri": $uri,
    "name": $name,
    "duration_ms": $duration_ms,
    "is_explicit": $is_explicit,
    "language": $language,
    "covers": $covers,
    "number": $number,
    "disc_number": $disc_number,
    "popularity": $popularity,
    "album": $album,
    "artists": $artists,
    "album_artists": $album_artists,
    "show_name": $show_name,
    "description": $description,
    "format": $format
  }' > "$EVENT_FILE"