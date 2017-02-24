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

#include "scene_lab/basic_camera.h"

namespace scene_lab {

using mathfu::vec2i;
using mathfu::vec2;
using mathfu::vec3;
using mathfu::vec4;
using mathfu::mat3;
using mathfu::mat4;

static const float kDefaultViewportAngle = 0.7853975f;  // 45 degrees
static const vec2 kViewportResolution = vec2(640, 480);
static const float kDefaultViewportNearPlane = 1.0f;
static const float kDefaultViewportFarPlane = 500.0f;

BasicCamera::BasicCamera()
    : position_(mathfu::kZeros3f),
      facing_(mathfu::kAxisY3f),
      up_(mathfu::kAxisZ3f) {
  Initialize(kDefaultViewportAngle, kViewportResolution,
             kDefaultViewportNearPlane, kDefaultViewportFarPlane);
}

// returns a matrix representing our camera.
// This is the "VP" of the MVP matrix we'll usually want.
// (The M is the world transform of the model.)
mathfu::mat4 BasicCamera::GetTransformMatrix() const {
  mat4 perspective_matrix_ = mat4::Perspective(
      viewport_angle_, viewport_resolution_.x / viewport_resolution_.y,
      viewport_near_plane_, viewport_far_plane_, 1.0f);

  // Subtract the facing vector because we need to be right handed.
  mat4 camera_matrix = mat4::LookAt(position_ - facing_, position_, up_);

  mat4 camera_transform = perspective_matrix_ * camera_matrix;

  return camera_transform;
}

// returns just the View matrix - doesn't do the projection transform.
mathfu::mat4 BasicCamera::GetViewMatrix() const {
  // Subtract the facing vector because we need to be right handed.
  return mat4::LookAt(position_ - facing_, position_, up_);
}

}  // namespace scene_lab
