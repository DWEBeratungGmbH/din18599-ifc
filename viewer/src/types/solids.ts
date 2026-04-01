/**
 * Solid Geometry Types for DIN 18599 Sidecar v2.1
 * 
 * Parametric solid geometry definitions for building elements.
 * Based on schema/solids.schema.json
 */

// ============================================================================
// Solid Types
// ============================================================================

export type SolidType = 
  | 'BOX' 
  | 'TRIANGULAR_PRISM' 
  | 'TRAPEZOIDAL_PRISM' 
  | 'PYRAMID_ROOF'

// ============================================================================
// Dimension Types
// ============================================================================

export interface BoxDimensions {
  length: number   // X-axis (East-West) in meters
  width: number    // Y-axis (North-South) in meters
  height: number   // Z-axis (vertical) in meters
}

export interface TriangularPrismDimensions {
  length: number              // X-axis (roof length) in meters
  width: number               // Y-axis (base of triangle) in meters
  height?: number             // Z-axis (ridge height) in meters
  slope?: number              // Roof slope in degrees (alternative to height)
  ridge_direction?: 'X' | 'Y' // Default: 'X'
  ridge_offset?: number       // Offset from center in meters (default: 0)
}

export interface TrapezoidalPrismDimensions {
  length: number                           // X-axis in meters
  width: number                            // Y-axis in meters
  height_low: number                       // Height at low side in meters
  height_high?: number                     // Height at high side in meters
  slope?: number                           // Roof slope in degrees (alternative to height_high)
  slope_direction?: 'N' | 'S' | 'E' | 'W' // Default: 'S'
}

export interface PyramidRoofDimensions {
  base_length: number       // Base length (X-axis) in meters
  base_width: number        // Base width (Y-axis) in meters
  height?: number           // Height of apex in meters
  slope?: number            // Roof slope in degrees (alternative to height)
  apex_offset?: [number, number] // Offset of apex from center [X, Y]
}

export type SolidDimensions = 
  | BoxDimensions 
  | TriangularPrismDimensions 
  | TrapezoidalPrismDimensions 
  | PyramidRoofDimensions

// ============================================================================
// Solid Base Interface
// ============================================================================

export interface SolidBase {
  id: string
  type: SolidType
  dimensions: SolidDimensions
  origin?: [number, number, number]  // Default: [0, 0, 0]
  parent_ref?: string
  offset?: [number, number, number]  // Default: [0, 0, 0]
  rotation?: number                  // Degrees around Z-axis, default: 0
  description?: string
}

// ============================================================================
// Specific Solid Types
// ============================================================================

export interface BoxSolid extends Omit<SolidBase, 'type' | 'dimensions'> {
  type: 'BOX'
  dimensions: BoxDimensions
}

export interface TriangularPrismSolid extends Omit<SolidBase, 'type' | 'dimensions'> {
  type: 'TRIANGULAR_PRISM'
  dimensions: TriangularPrismDimensions
}

export interface TrapezoidalPrismSolid extends Omit<SolidBase, 'type' | 'dimensions'> {
  type: 'TRAPEZOIDAL_PRISM'
  dimensions: TrapezoidalPrismDimensions
}

export interface PyramidRoofSolid extends Omit<SolidBase, 'type' | 'dimensions'> {
  type: 'PYRAMID_ROOF'
  dimensions: PyramidRoofDimensions
}

export type Solid = BoxSolid | TriangularPrismSolid | TrapezoidalPrismSolid | PyramidRoofSolid

// ============================================================================
// Geometry Section
// ============================================================================

export interface CoordinateSystem {
  type: 'PROJECT_NORTH'
  x_axis?: string  // Default: 'EAST (Project)'
  y_axis?: string  // Default: 'NORTH (Project)'
  z_axis?: string  // Default: 'UP'
  unit?: 'METER' | 'MILLIMETER'  // Default: 'METER'
}

export interface GeometrySection {
  coordinate_system?: CoordinateSystem
  solids: Solid[]
}

// ============================================================================
// Site Section
// ============================================================================

export interface SiteSection {
  address?: string
  latitude?: number
  longitude?: number
  true_north_offset?: number  // Default: 0
  description?: string
}

// ============================================================================
// Face Reference
// ============================================================================

export interface FaceReference {
  solid_ref: string
  face_index: number
}

// ============================================================================
// Computed Geometry (not in JSON, calculated at runtime)
// ============================================================================

export interface Face {
  index: number
  normal: [number, number, number]  // Normalized normal vector
  vertices: [number, number, number][]  // Vertex positions
  area: number  // Calculated area in m²
  type: 'WALL' | 'ROOF' | 'FLOOR' | 'CEILING'
}

export interface ComputedSolidGeometry {
  solid: Solid
  vertices: [number, number, number][]
  faces: Face[]
  volume: number  // m³
  worldPosition: [number, number, number]  // Absolute position after parent transforms
}

// ============================================================================
// Orientation Calculation Result
// ============================================================================

export interface OrientationResult {
  project_north: number  // Angle in project north system (0-360°)
  true_north: number     // Angle in geographic north system (0-360°)
  inclination: number    // Angle from horizontal (0=horizontal, 90=vertical)
}

// ============================================================================
// Type Guards
// ============================================================================

export function isBoxSolid(solid: Solid): solid is BoxSolid {
  return solid.type === 'BOX'
}

export function isTriangularPrismSolid(solid: Solid): solid is TriangularPrismSolid {
  return solid.type === 'TRIANGULAR_PRISM'
}

export function isTrapezoidalPrismSolid(solid: Solid): solid is TrapezoidalPrismSolid {
  return solid.type === 'TRAPEZOIDAL_PRISM'
}

export function isPyramidRoofSolid(solid: Solid): solid is PyramidRoofSolid {
  return solid.type === 'PYRAMID_ROOF'
}

// ============================================================================
// Defaults
// ============================================================================

export const DEFAULT_COORDINATE_SYSTEM: CoordinateSystem = {
  type: 'PROJECT_NORTH',
  x_axis: 'EAST (Project)',
  y_axis: 'NORTH (Project)',
  z_axis: 'UP',
  unit: 'METER'
}

export const DEFAULT_SITE: SiteSection = {
  true_north_offset: 0
}

export const DEFAULT_ORIGIN: [number, number, number] = [0, 0, 0]
export const DEFAULT_OFFSET: [number, number, number] = [0, 0, 0]
export const DEFAULT_ROTATION = 0
