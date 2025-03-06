from pantheon_v2.core.common.tests.test_models import TestModel, TestModel2, TestModel3


def test_generic_base_model():
    test_model = TestModel(name="test")
    test_model2 = TestModel2(name="test2", test_model=test_model)
    test_model3 = TestModel3(name="test3", test_model=test_model2)

    assert test_model3.test_model.test_model.name == "test"

    test_model3_dict = test_model3.model_dump()
    assert (
        test_model3_dict["__test_model_type"]
        == "pantheon_v2.core.common.tests.test_models.TestModel2"
    )
    assert (
        test_model3_dict["test_model"]["__test_model_type"]
        == "pantheon_v2.core.common.tests.test_models.TestModel"
    )
    assert test_model3_dict["test_model"]["test_model"]["name"] == "test"

    test_model3_dict_2 = TestModel3.model_validate(test_model3_dict)
    assert test_model3_dict_2.test_model.test_model.name == "test"
