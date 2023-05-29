import vtk
from ErrorObserver import *
from NiiObject import *
from config import *
from NiiLabel import *

error_observer = ErrorObserver()



def read_volume(file_name):
    
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileNameSliceOffset(1)
    reader.SetDataByteOrderToBigEndian()
    reader.SetFileName(file_name)
    reader.Update()
    return reader


def create_liver_extractor(liver):
   
    liver_extractor = vtk.vtkFlyingEdges3D()
    liver_extractor.SetInputConnection(liver.reader.GetOutputPort())
    # liver_extractor.SetValue(0, sum(liver.scalar_range)/2)
    return liver_extractor


def create_mask_extractor(mask):
   
    mask_extractor = vtk.vtkDiscreteMarchingCubes()
    mask_extractor.SetInputConnection(mask.reader.GetOutputPort())
    return mask_extractor


def create_polygon_reducer(extractor):
  
    reducer = vtk.vtkDecimatePro()
    reducer.AddObserver('ErrorEvent', error_observer)  # throws an error event if there is no data to decimate
    reducer.SetInputConnection(extractor.GetOutputPort())
    reducer.SetTargetReduction(0.5)  # magic number
    reducer.PreserveTopologyOn()
    return reducer


def create_smoother(reducer, smoothness):
   
    smoother = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputConnection(reducer.GetOutputPort())
    smoother.SetNumberOfIterations(smoothness)
    return smoother


def create_normals(smoother):
  
    liver_normals = vtk.vtkPolyDataNormals()
    liver_normals.SetInputConnection(smoother.GetOutputPort())
    liver_normals.SetFeatureAngle(60.0)  #
    return liver_normals


def create_mapper(stripper):
    liver_mapper = vtk.vtkPolyDataMapper()
    liver_mapper.SetInputConnection(stripper.GetOutputPort())
    liver_mapper.ScalarVisibilityOff()
    liver_mapper.Update()
    return liver_mapper


def create_property(opacity, color):
    prop = vtk.vtkProperty()
    prop.SetColor(color[0], color[1], color[2])
    prop.SetOpacity(opacity)
    return prop


def create_actor(mapper, prop):
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetProperty(prop)
    return actor


def create_mask_table():
    m_mask_opacity = 1
    liver_lut = vtk.vtkLookupTable()
    liver_lut.SetRange(0, 4)
    liver_lut.SetRampToLinear()
    liver_lut.SetValueRange(0, 1)
    liver_lut.SetHueRange(0, 0)
    liver_lut.SetSaturationRange(0, 0)

    liver_lut.SetNumberOfTableValues(10)
    liver_lut.SetTableRange(0, 9)
    liver_lut.SetTableValue(0, 0, 0, 0, 0)
    liver_lut.SetTableValue(1, 1, 0, 0, m_mask_opacity)  # RED
    liver_lut.SetTableValue(2, 0, 1, 0, m_mask_opacity)  # GREEN
    liver_lut.SetTableValue(3, 1, 1, 0, m_mask_opacity)  # YELLOW
    liver_lut.SetTableValue(4, 0, 0, 1, m_mask_opacity)  # BLUE
    liver_lut.SetTableValue(5, 1, 0, 1, m_mask_opacity)  # MAGENTA
    liver_lut.SetTableValue(6, 0, 1, 1, m_mask_opacity)  # CYAN
    liver_lut.SetTableValue(7, 1, 0.5, 0.5, m_mask_opacity)  # RED_2
    liver_lut.SetTableValue(8, 0.5, 1, 0.5, m_mask_opacity)  # GREEN_2
    liver_lut.SetTableValue(9, 0.5, 0.5, 1, m_mask_opacity)  # BLUE_2
    liver_lut.Build()
    return liver_lut


def create_table():
    table = vtk.vtkLookupTable()
    table.SetRange(0.0, 1675.0)  # +1
    table.SetRampToLinear()
    table.SetValueRange(0, 1)
    table.SetHueRange(0, 0)
    table.SetSaturationRange(0, 0)


def add_surface_rendering(nii_object, label_idx, label_value):
    nii_object.labels[label_idx].extractor.SetValue(0, label_value)
    nii_object.labels[label_idx].extractor.Update()

    # if the cell size is 0 then there is no label_idx data
    if nii_object.labels[label_idx].extractor.GetOutput().GetMaxCellSize():
        reducer = create_polygon_reducer(nii_object.labels[label_idx].extractor)
        smoother = create_smoother(reducer, nii_object.labels[label_idx].smoothness)
        normals = create_normals(smoother)
        actor_mapper = create_mapper(normals)
        actor_property = create_property(nii_object.labels[label_idx].opacity, nii_object.labels[label_idx].color)
        actor = create_actor(actor_mapper, actor_property)
        nii_object.labels[label_idx].actor = actor
        nii_object.labels[label_idx].smoother = smoother
        nii_object.labels[label_idx].property = actor_property


def setup_slicer(renderer, liver):
    x = liver.extent[1]
    y = liver.extent[3]
    z = liver.extent[5]

    axial = vtk.vtkImageActor()
    axial_prop = vtk.vtkImageProperty()
    axial_prop.SetOpacity(0)
    axial.SetProperty(axial_prop)
    axial.GetMapper().SetInputConnection(liver.image_mapper.GetOutputPort())
    axial.SetDisplayExtent(0, x, 0, y, int(z/2), int(z/2))
    axial.InterpolateOn()
    axial.ForceOpaqueOn()

    coronal = vtk.vtkImageActor()
    cor_prop = vtk.vtkImageProperty()
    cor_prop.SetOpacity(0)
    coronal.SetProperty(cor_prop)
    coronal.GetMapper().SetInputConnection(liver.image_mapper.GetOutputPort())
    coronal.SetDisplayExtent(0, x, int(y/2), int(y/2), 0, z)
    coronal.InterpolateOn()
    coronal.ForceOpaqueOn()

    sagittal = vtk.vtkImageActor()
    sag_prop = vtk.vtkImageProperty()
    sag_prop.SetOpacity(0)
    sagittal.SetProperty(sag_prop)
    sagittal.GetMapper().SetInputConnection(liver.image_mapper.GetOutputPort())
    sagittal.SetDisplayExtent(int(x/2), int(x/2), 0, y, 0, z)
    sagittal.InterpolateOn()
    sagittal.ForceOpaqueOn()

    renderer.AddActor(axial)
    renderer.AddActor(coronal)
    renderer.AddActor(sagittal)

    return [axial, coronal, sagittal]


def setup_projection(liver, renderer):
    slice_mapper = vtk.vtkImageResliceMapper()
    slice_mapper.SetInputConnection(liver.reader.GetOutputPort())
    slice_mapper.SliceFacesCameraOn()
    slice_mapper.SliceAtFocalPointOn()
    slice_mapper.BorderOff()

    liver_image_prop = vtk.vtkImageProperty()
    liver_image_prop.SetOpacity(0.0)
    liver_image_prop.SetInterpolationTypeToLinear()
    image_slice = vtk.vtkImageSlice()
    image_slice.SetMapper(slice_mapper)
    image_slice.SetProperty(liver_image_prop)
    image_slice.GetMapper().SetInputConnection(liver.image_mapper.GetOutputPort())
    renderer.AddViewProp(image_slice)
    return liver_image_prop


def setup_liver(renderer, file):
    liver = NiiObject()
    liver.file = file
    liver.reader = read_volume(liver.file)
    liver.labels.append(NiiLabel(liver_COLORS[0], liver_OPACITY, liver_SMOOTHNESS))
    liver.labels[0].extractor = create_liver_extractor(liver)
    liver.extent = liver.reader.GetDataExtent()

    scalar_range = liver.reader.GetOutput().GetScalarRange()
    bw_lut = vtk.vtkLookupTable()
    bw_lut.SetTableRange(scalar_range)
    bw_lut.SetSaturationRange(0, 0)
    bw_lut.SetHueRange(0, 0)
    bw_lut.SetValueRange(0, 2)
    bw_lut.Build()

    view_colors = vtk.vtkImageMapToColors()
    view_colors.SetInputConnection(liver.reader.GetOutputPort())
    view_colors.SetLookupTable(bw_lut)
    view_colors.Update()
    liver.image_mapper = view_colors
    liver.scalar_range = scalar_range

    add_surface_rendering(liver, 0, sum(scalar_range)/2)  # render index, default extractor value
    renderer.AddActor(liver.labels[0].actor)
    return liver


def setup_mask(renderer, file):
    mask = NiiObject()
    mask.file = file
    mask.reader = read_volume(mask.file)
    mask.extent = mask.reader.GetDataExtent()
    n_labels = int(mask.reader.GetOutput().GetScalarRange()[1])
    n_labels = n_labels if n_labels <= 10 else 10

    for label_idx in range(n_labels):
        mask.labels.append(NiiLabel(MASK_COLORS[label_idx], MASK_OPACITY, MASK_SMOOTHNESS))
        mask.labels[label_idx].extractor = create_mask_extractor(mask)
        add_surface_rendering(mask, label_idx, label_idx + 1)
        renderer.AddActor(mask.labels[label_idx].actor)
    return mask