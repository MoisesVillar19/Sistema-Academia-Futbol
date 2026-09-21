import customtkinter as ctk
from tkinter import messagebox
from controllers import usuario_controller
from controllers import login_controller


class CrearUsuarioDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Nuevo Usuario")
        self.geometry("440x420")
        self.resizable(False, False)
        self.configure(fg_color="#F8F5FA")
        self.grab_set()
        self.on_save = on_save
        self._centrar()
        self._crear_widgets()

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 220
        y = (self.winfo_screenheight() // 2) - 210
        self.geometry(f"440x420+{x}+{y}")

    def _crear_widgets(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=25, pady=20)

        ctk.CTkLabel(
            frame, text="Nuevo Usuario",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#3D1559",
        ).pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(frame, text="DNI de la persona:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_dni = ctk.CTkEntry(frame, width=390, height=38, placeholder_text="8 dígitos")
        self.entry_dni.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(frame, text="Nombre de usuario:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_username = ctk.CTkEntry(frame, width=390, height=38, placeholder_text="Username")
        self.entry_username.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(frame, text="Rol:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        ctk.CTkLabel(frame, text="ADMIN: acceso total | SECRETARIA: academia, finanzas e inventario (sin Usuarios, Tarifas, Auditoría ni Configuración)", font=ctk.CTkFont(size=10), text_color="gray", wraplength=380, justify="left").pack(anchor="w")
        self.combo_rol = ctk.CTkComboBox(
            frame, values=["ADMIN", "SECRETARIA"], width=390, height=38,
        )
        self.combo_rol.set("SECRETARIA")
        self.combo_rol.pack(anchor="w", pady=(0, 15))

        self.label_status = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11))
        self.label_status.pack(anchor="w", pady=(0, 5))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=(5, 0))

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=180, height=40,
            fg_color="#6c757d", hover_color="#5a6268",
            corner_radius=8, command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Crear Usuario", width=180, height=40,
            fg_color="#7C3AED", hover_color="#6D28D9",
            corner_radius=8, command=self._guardar,
        ).pack(side="left", padx=5)

        self.entry_dni.bind("<Return>", lambda e: self._guardar())
        self.entry_username.bind("<Return>", lambda e: self._guardar())

    def _guardar(self):
        dni = self.entry_dni.get().strip()
        username = self.entry_username.get().strip()
        rol = self.combo_rol.get()

        if not username:
            self.label_status.configure(text="El username es obligatorio", text_color="red")
            return

        if not dni:
            self.label_status.configure(text="El DNI es obligatorio", text_color="red")
            return

        persona_data = {
            "dni": dni,
            "nombres": "",
            "apellidos": "",
        }

        exito, msg, id_usuario = usuario_controller.crear_usuario(persona_data, username, rol)

        if exito:
            messagebox.showinfo(
                "Usuario Creado",
                f"Usuario: {username}\n\n"
                f"Contraseña temporal: {msg}\n\n"
                f"El usuario debe cambiarla al iniciar sesión.",
            )
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            self.label_status.configure(text=msg, text_color="red")


class EditarUsuarioDialog(ctk.CTkToplevel):
    def __init__(self, parent, usuario, on_save=None):
        super().__init__(parent)
        self.title(f"Editar Usuario - {usuario['username']}")
        self.geometry("440x520")
        self.resizable(False, False)
        self.configure(fg_color="#F8F5FA")
        self.grab_set()
        self.usuario = usuario
        self.on_save = on_save
        self._centrar()
        self._crear_widgets()

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 220
        y = (self.winfo_screenheight() // 2) - 260
        self.geometry(f"440x520+{x}+{y}")

    def _crear_widgets(self):
        frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=25, pady=20)

        ctk.CTkLabel(
            frame, text="Editar Usuario",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#3D1559",
        ).pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(frame, text="Username:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_username = ctk.CTkEntry(frame, width=340, height=38)
        self.entry_username.insert(0, self.usuario.get("username", ""))
        self.entry_username.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(frame, text="Rol:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        ctk.CTkLabel(frame, text="ADMIN: acceso total | SECRETARIA: academia, finanzas e inventario (sin Usuarios, Tarifas, Auditoría ni Configuración)", font=ctk.CTkFont(size=10), text_color="gray", wraplength=330, justify="left").pack(anchor="w")
        self.combo_rol = ctk.CTkComboBox(
            frame, values=["ADMIN", "SECRETARIA"], width=340, height=38,
        )
        self.combo_rol.set(self.usuario.get("rol", "SECRETARIA"))
        self.combo_rol.pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(
            frame, text="Restablecer Contraseña",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3D1559",
        ).pack(anchor="w", pady=(5, 5))

        ctk.CTkLabel(
            frame, text="Deje vacío para mantener la contraseña actual",
            font=ctk.CTkFont(size=11), text_color="gray",
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(frame, text="Nueva contraseña:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_password = ctk.CTkEntry(frame, width=340, height=38, show="•")
        self.entry_password.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(frame, text="Confirmar contraseña:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_confirm = ctk.CTkEntry(frame, width=340, height=38, show="•")
        self.entry_confirm.pack(anchor="w", pady=(0, 10))

        self.label_status = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11))
        self.label_status.pack(anchor="w", pady=(0, 5))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=(5, 0))

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=150, height=40,
            fg_color="#6c757d", hover_color="#5a6268",
            corner_radius=8, command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Guardar", width=150, height=40,
            fg_color="#7C3AED", hover_color="#6D28D9",
            corner_radius=8, command=self._guardar,
        ).pack(side="left", padx=5)

        self.entry_password.bind("<Return>", lambda e: self._guardar())
        self.entry_confirm.bind("<Return>", lambda e: self._guardar())

    def _guardar(self):
        username = self.entry_username.get().strip()
        rol = self.combo_rol.get()
        nueva_pass = self.entry_password.get().strip()
        confirm_pass = self.entry_confirm.get().strip()

        if not username:
            self.label_status.configure(text="El username es obligatorio", text_color="red")
            return

        if nueva_pass:
            if len(nueva_pass) < 6:
                self.label_status.configure(text="La contraseña debe tener al menos 6 caracteres", text_color="red")
                return
            if nueva_pass != confirm_pass:
                self.label_status.configure(text="Las contraseñas no coinciden", text_color="red")
                return

        data = {"username": username, "rol": rol}
        if nueva_pass:
            data["password"] = nueva_pass
        exito, msg = usuario_controller.editar_usuario(
            self.usuario["id_usuario"], data,
        )

        if exito:
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente")
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            self.label_status.configure(text=msg, text_color="red")


class MiPerfilDialog(ctk.CTkToplevel):
    """Bloque C2: diálogo Mi perfil para TODOS los roles.

    Muestra datos del usuario en sesión y permite cambiar su contraseña
    vía ``login_controller.cambiar_password``.

    Nota: no reutiliza ``CambiarPasswordView`` porque esa vista es de flujo
    obligatorio de primer acceso (su ``_on_cerrar`` hace ``sys.exit``);
    incrustarla aquí cerraría la app al descartar el diálogo.
    """

    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Mi Perfil")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(fg_color="#F8F5FA")
        self.transient(parent)
        self.grab_set()
        self.on_save = on_save
        self._centrar()
        self._crear_widgets()

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 220
        y = (self.winfo_screenheight() // 2) - 280
        self.geometry(f"440x560+{x}+{y}")

    def _crear_widgets(self):
        from controllers import login_controller

        usuario = login_controller.obtener_usuario_actual() or {}
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=25, pady=20)

        ctk.CTkLabel(
            scroll, text="Mi Perfil",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#3D1559",
        ).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(
            scroll,
            text=f"{usuario.get('nombres', '')} {usuario.get('apellidos', '')}".strip() or usuario.get("username", ""),
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(anchor="w", pady=(0, 10))

        for etiqueta, valor in (
            ("Nombres:", usuario.get("nombres", "")),
            ("Apellidos:", usuario.get("apellidos", "")),
            ("DNI:", usuario.get("dni", "")),
            ("Usuario:", usuario.get("username", "")),
            ("Rol:", usuario.get("rol", "")),
        ):
            ctk.CTkLabel(scroll, text=etiqueta, font=ctk.CTkFont(size=12)).pack(anchor="w")
            entry = ctk.CTkEntry(scroll, width=340, height=34, state="disabled")
            entry.pack(anchor="w", pady=(0, 8))
            # CTkEntry disabled ignora insert en algunas versiones: habilitar, insertar, deshabilitar
            try:
                entry.configure(state="normal")
                entry.insert(0, str(valor or ""))
                entry.configure(state="disabled")
            except Exception:
                pass

        ctk.CTkLabel(
            scroll, text="Cambiar Contraseña",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3D1559",
        ).pack(anchor="w", pady=(8, 5))

        ctk.CTkLabel(scroll, text="Contraseña actual:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_actual = ctk.CTkEntry(scroll, width=340, height=38, show="•")
        self.entry_actual.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(scroll, text="Nueva contraseña (mín. 6 caracteres):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_nueva = ctk.CTkEntry(scroll, width=340, height=38, show="•")
        self.entry_nueva.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(scroll, text="Confirmar nueva contraseña:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.entry_confirm = ctk.CTkEntry(scroll, width=340, height=38, show="•")
        self.entry_confirm.pack(anchor="w", pady=(0, 10))

        self.label_status = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=11))
        self.label_status.pack(anchor="w", pady=(0, 5))

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=(5, 0))

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=150, height=40,
            fg_color="#6c757d", hover_color="#5a6268",
            corner_radius=8, command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Guardar", width=150, height=40,
            fg_color="#7C3AED", hover_color="#6D28D9",
            corner_radius=8, command=self._guardar,
        ).pack(side="left", padx=5)

    def _guardar(self):
        from controllers import login_controller
        exito, msg = login_controller.cambiar_password(
            self.entry_actual.get().strip(),
            self.entry_nueva.get().strip(),
            self.entry_confirm.get().strip(),
        )
        try:
            self.label_status.configure(text=msg, text_color="green" if exito else "red")
        except Exception:
            pass
        if exito:
            if self.on_save:
                self.on_save()
            self.after(600, self.destroy)


class UsuarioView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._crear_widgets()
        self._cargar_usuarios()

    def _crear_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_usuarios = self.tabview.add("Usuarios")
        self.tab_permisos = self.tabview.add("Permisos por rol")

        header = ctk.CTkFrame(self.tab_usuarios, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header, text="Gestión de Usuarios",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ Nuevo Usuario", width=150,
            command=self._abrir_formulario,
        ).pack(side="right")

        filtros = ctk.CTkFrame(self.tab_usuarios, fg_color="transparent")
        filtros.pack(fill="x", padx=10, pady=5)

        self.filtro_estado = ctk.CTkSegmentedButton(
            filtros, values=["Todos", "Activos", "Inactivos"],
            command=self._filtrar,
        )
        self.filtro_estado.set("Todos")
        self.filtro_estado.pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_usuarios)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.label_status = ctk.CTkLabel(self.tab_usuarios, text="", font=ctk.CTkFont(size=11))
        self.label_status.pack(pady=5)

        self._crear_tab_permisos()

    def _crear_tab_permisos(self):
        from utils.ui_helpers import crear_seccion, crear_nota, crear_boton_interactivo
        sec = crear_seccion(
            self.tab_permisos, titulo="Permisos del rol SECRETARIA", icono="🔑",
            descripcion="Tilda los módulos visibles. ADMIN siempre tiene acceso total (fijo). Aplica al próximo login.",
            nro=1,
        )
        crear_nota(sec, "Si quitas Pagos o Ventas a SECRETARIA, esas opciones desaparecen de su menú.")
        self._vars_permisos = {}
        grid = ctk.CTkFrame(sec, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 8))
        try:
            from utils.constants import MODULOS_SISTEMA
        except Exception:
            MODULOS_SISTEMA = ("dashboard", "estudiantes", "matriculas", "pagos", "ventas",
                               "inventario", "reportes", "egresos", "importar", "usuarios",
                               "tarifas", "auditoria", "configuracion", "respaldo")
        actuales = usuario_controller.listar_permisos_rol("SECRETARIA")
        for i, mod in enumerate(MODULOS_SISTEMA):
            var = ctk.BooleanVar(value=(mod in actuales))
            chk = ctk.CTkCheckBox(grid, text=mod.capitalize(), variable=var)
            chk.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=3)
            self._vars_permisos[mod] = var
        self.label_permisos_status = ctk.CTkLabel(sec, text="", font=ctk.CTkFont(size=11))
        self.label_permisos_status.pack(anchor="w", padx=10, pady=2)
        crear_boton_interactivo(sec, text="Guardar permisos", width=160,
                                command=self._guardar_permisos, fg_color="#7C3AED").pack(anchor="w", padx=10, pady=6)

    def _guardar_permisos(self):
        elegidos = [m for m, v in self._vars_permisos.items() if v.get()]
        exito, msg = usuario_controller.guardar_permisos_rol("SECRETARIA", elegidos)
        try:
            self.label_permisos_status.configure(text=msg, text_color="green" if exito else "red")
        except Exception:
            pass

    def _cargar_usuarios(self, activo=None):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        usuarios = usuario_controller.listar_usuarios(activo=activo)

        if not usuarios:
            ctk.CTkLabel(
                self.scroll_frame, text="No hay usuarios registrados",
                text_color="gray",
            ).pack(pady=20)
            return

        for usuario in usuarios:
            self._crear_card(usuario)

        self.label_status.configure(text=f"Total: {len(usuarios)} usuario(s)")

    def _crear_card(self, usuario):
        card = ctk.CTkFrame(self.scroll_frame)
        card.pack(fill="x", padx=5, pady=3)

        estado_color = "green" if usuario["activo"] else "red"
        estado_text = "Activo" if usuario["activo"] else "Inactivo"

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        ctk.CTkLabel(
            info, text=f"{usuario['username']}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=f"Rol: {usuario['rol']}  |  Estado: {estado_text}",
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(anchor="w")

        botones = ctk.CTkFrame(card, fg_color="transparent")
        botones.pack(side="right", padx=5, pady=5)

        ctk.CTkButton(
            botones, text="Editar", width=80, height=30,
            command=lambda u=usuario: self._editar(u),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            botones, text="Restablecer", width=100, height=30,
            fg_color="orange", hover_color="darkorange",
            command=lambda u=usuario: self._restablecer(u),
        ).pack(side="left", padx=2)

        if usuario["activo"]:
            ctk.CTkButton(
                botones, text="Desactivar", width=90, height=30,
                fg_color="red", hover_color="darkred",
                command=lambda u=usuario: self._desactivar(u),
            ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(
                botones, text="Activar", width=90, height=30,
                fg_color="green", hover_color="darkgreen",
                command=lambda u=usuario: self._activar(u),
            ).pack(side="left", padx=2)

    def _filtrar(self, valor):
        if valor == "Activos":
            self._cargar_usuarios(activo=1)
        elif valor == "Inactivos":
            self._cargar_usuarios(activo=0)
        else:
            self._cargar_usuarios()

    def _editar(self, usuario):
        EditarUsuarioDialog(self, usuario, on_save=self._cargar_usuarios)

    def _restablecer(self, usuario):
        exito, mensaje, temp_pass = usuario_controller.restablecer_password(usuario["id_usuario"])
        if exito:
            messagebox.showinfo(
                "Contraseña Restablecida",
                f"Usuario: {usuario['username']}\n\n"
                f"Nueva contraseña temporal:\n{temp_pass}\n\n"
                f"El usuario debe cambiarla al iniciar sesión.",
            )

    def _abrir_formulario(self):
        CrearUsuarioDialog(self, on_save=self._cargar_usuarios)

    def _activar(self, usuario):
        exito, mensaje = usuario_controller.activar_usuario(usuario["id_usuario"])
        if exito:
            self._cargar_usuarios()

    def _desactivar(self, usuario):
        exito, mensaje = usuario_controller.desactivar_usuario(usuario["id_usuario"])
        if exito:
            self._cargar_usuarios()
