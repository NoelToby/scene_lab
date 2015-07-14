// Copyright 2015 Google Inc. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef FPL_EVENTS_EDITOREVENT_H_
#define FPL_EVENTS_EDITOREVENT_H_

#include "entity/entity_manager.h"
#include "event/event_registry.h"
#include "mathfu/vector.h"
#include "editor_events_generated.h"

namespace fpl {
namespace editor {

struct EditorEventPayload {
  EditorEventPayload(EditorEventAction _action) : action(_action) {}
  EditorEventPayload(EditorEventAction _action,
                     const entity::EntityRef& _entity)
      : action(_action), entity(_entity) {}

  EditorEventAction action;
  entity::EntityRef entity;
};

}  // fpl_project
}  // fpl

// TODO(amablue): allow events to exist in libraries without requiring them to
// use
// enums from the main project. Use entity system as an example?
const int kEventSinkUnion_EditorEvent = 5;
FPL_REGISTER_EVENT_PAYLOAD_ID(kEventSinkUnion_EditorEvent,
                              fpl::editor::EditorEventPayload)

#endif  // FPL_EVENTS_EDITOREVENT_H_
