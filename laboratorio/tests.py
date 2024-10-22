from django.test import TestCase
from laboratorio.models import Laboratorio, Producto, DirectorGeneral
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from datetime import date

# Create your tests here.
# command python manage.py test <app_name>

class LabModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.test_entry = Laboratorio.objects.create(**{"nombre": "labtest", "ciudad": "quilpué", "país": "chile"})

    # test para ver si la db creada al hacer test
    # tiene los mismos datos que la db de producción
    def test_db_matches_created_db(self):
        entry = Laboratorio.objects.get(pk=self.test_entry.id)
        self.assertEqual(entry.nombre, "LABTEST")


    def test_lab_list_page_response(self):
        # reverse returns a str
        url = reverse("lab:labs")
        # mimics a request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_labList_correct_tamplate(self):
        url = reverse("lab:labs")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "laboratorio/list.html")

    def test_labList_page_content(self):
        # create an entry for this test
        # ccreate returns the created object
        url = reverse("lab:labs")
        response = self.client.get(url)
        self.assertContains(response, self.test_entry.nombre)


class ChangeTableViewTest(TestCase):

    def test_error_if_not_htmx_request(self):
        url = reverse("lab:other-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_ok_if_htmx_request_has_header(self):
        headers = {'HTTP_HX_REQUEST': 'true'}
        url = reverse("lab:other-list")
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 200)

    def test_get_correct_table(self):
        headers = {'HTTP_HX_REQUEST': 'true'}
        test_values = [{"change": f"{i}"} for i in range(1, 4)]
        contents = ["laboratorios", "directores", "productos"]
        for url_table in zip(test_values, contents):
           url = reverse("lab:other-list")
           # first url queries (?val=x) then headers
           response = self.client.get(url, url_table[0], **headers)
           self.assertTemplateUsed(response, "laboratorio/change_list.html")
           self.assertContains(response, url_table[1])


class DeleteViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase (the class)
        # run once at the beginning
        cls.new_user = User.objects.create_user(username='testuser', password='12345')
        cls.new_user.user_permissions.add(Permission.objects.get(codename='delete_producto'))
        cls.test_entry = Laboratorio.objects.create(**{"nombre": "labtest", "ciudad": "quilpué", "país": "chile"})
        cls.deletable_entry = Producto.objects.create(**{"nombre": "testcure", "laboratorio": cls.test_entry, 
                                                         "fecha_fabricación": date.today(), "costo_producto": 126, "venta_producto": 450})
    # runs before each test
    def setUp(self):
        self.client.login(username="testuser", password="12345")

    def test_error_if_not_htmx_request_delete(self):
        url = reverse("lab:delete", kwargs={"tabla": 1, "pk": 78})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_model_deletion(self):
        headers = {'HTTP_HX_REQUEST': 'true'}
        url = reverse("lab:delete", kwargs={"tabla": 3, "pk": self.deletable_entry.pk})
        response = self.client.delete(url, **headers)
        self.assertQuerySetEqual(Producto.objects.filter(nombre="testcure"), [])
        self.assertRedirects(response, expected_url=reverse("lab:other-list") + f"?change=3")


class UpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase (the class)
        # run once at the beginning
        cls.new_user = User.objects.create_user(username='testuser', password='12345')
        cls.new_user.user_permissions.add(Permission.objects.get(codename='change_directorgeneral'))
        cls.new_user.user_permissions.add(Permission.objects.get(codename='change_producto'))
        cls.test_entry = Laboratorio.objects.create(**{"nombre": "labtest2", "ciudad": "quilpué", "país": "chile"})
        cls.deletable_entry = DirectorGeneral.objects.create(**{"nombre": "Jean", "especialidad": "tester", "laboratorio": cls.test_entry})
        cls.deletable_entry2 = Producto.objects.create(**{"nombre": "testcure", "laboratorio": cls.test_entry, 
                                                         "fecha_fabricación": date.today(), "costo_producto": 126, "venta_producto": 450})
    # runs before each test
    def setUp(self):
        self.client.login(username="testuser", password="12345")

    def test_error_if_not_htmx_request_update(self):
        url = reverse("lab:update", kwargs={"tabla": 2, "pk": self.deletable_entry.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_model_update(self):
        headers = {'HTTP_HX_REQUEST': 'true'}
        # to recreate a form update with relations pass as the relation the pk of the related instance
        data = {"nombre": "Jean", "especialidad": "mastertester", "laboratorio": self.test_entry.pk}
        url = reverse("lab:update", kwargs={"tabla": 2, "pk": self.deletable_entry.pk})
        self.client.post(url, data, **headers)
        # reload object after update
        self.assertEqual(DirectorGeneral.objects.get(pk=self.deletable_entry.pk).especialidad, data["especialidad"].upper())

    def test_model_update_with_error(self):
        headers = {'HTTP_HX_REQUEST': 'true'}
        # for data field pass it like this
        data = {"nombre": "testcure", "laboratorio": self.test_entry.pk, "fecha_fabricación": "2016-07-29", "costo_producto": 700, "venta_producto": 450}
        url = reverse("lab:update", kwargs={"tabla": 3, "pk": self.deletable_entry2.pk})
        response = self.client.post(url, data, **headers)
        # reload object after update
        self.assertContains(response, "no puede ser menor")    

    

class CreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase (the class)
        # run once at the beginning
        cls.new_user = User.objects.create_user(username='testuser', password='12345')
        cls.new_user.user_permissions.add(Permission.objects.get(codename='add_laboratorio'))
        cls.test_entry = Laboratorio.objects.create(**{"nombre": "labtest2", "ciudad": "arica", "país": "chile"})

    def setUp(self):
        self.client.login(username="testuser", password="12345")

    def test_error_if_not_htmx_request_create(self):
        url = reverse("lab:add", kwargs={"tabla": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_model_creation(self):
        headers = {'HTTP_HX_REQUEST': 'true'}
        data = {"nombre": "lablab", "ciudad": "quellon", "país": "chile"}
        url = reverse("lab:add", kwargs={"tabla": 1})
        self.client.post(url, data, **headers)
        # entry name is saved using its upper form
        self.assertEqual(Laboratorio.objects.filter(nombre=data["nombre"].upper())[0].nombre, "LABLAB")

    def test_model_creation_with_errors(self):
        headers = {'HTTP_HX_REQUEST': 'true'}
        data = {"nombre": self.test_entry.nombre, "ciudad": "quellon", "país": "chile"}
        url = reverse("lab:add", kwargs={"tabla": 1})
        response = self.client.post(url, data, **headers)
        self.assertContains(response, "nombre del laboratorio ya existe") 

