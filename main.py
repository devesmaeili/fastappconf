import os
from typing import List, Optional

from fastapi import FastAPI, applications
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

import fastapi_offline_swagger_ui


class FastAppConf:
    """
    Configuration class for setting up a FastAPI application with options
    for CORS, static file mounting, and custom Swagger UI.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        version: Optional[str] = None,
        openapi_prefix: Optional[str] = None,
        openapi_url: Optional[str] = None,
        assets_url: Optional[str] = None,
        docs_url: Optional[str] = None,
        swagger_css_url: Optional[str] = None,
        swagger_js_url: Optional[str] = None,
        swagger_favicon_url: Optional[str] = None,
        origins: Optional[List[str]] = None,
        static_dirs: Optional[List[str]] = None,
    ) -> None:
        """
        Initializes the FastAppConf instance with various FastAPI and Swagger settings.

        Args:
            title: Title of the FastAPI app.
            version: Version of the FastAPI app.
            openapi_prefix: Prefix for OpenAPI endpoints.
            openapi_url: URL path to access the OpenAPI schema.
            assets_url: URL to serve Swagger UI assets.
            docs_url: URL path to serve Swagger documentation.
            swagger_css_url: Custom URL to Swagger CSS.
            swagger_js_url: Custom URL to Swagger JS.
            swagger_favicon_url: Custom URL to Swagger favicon.
            origins: List of allowed CORS origins.
            static_dirs: List of directories to serve static files from.
        """
        self.title = title
        self.version = version
        self.openapi_prefix = openapi_prefix
        self.openapi_url = openapi_url
        self.assets_url = assets_url
        self.docs_url = docs_url
        self.swagger_css_url = swagger_css_url
        self.swagger_js_url = swagger_js_url
        self.swagger_favicon_url = swagger_favicon_url
        self.origins = origins or []
        self.static_dirs = static_dirs or []
        self.app: Optional[FastAPI] = None

    def setup(self, lifespan=None) -> FastAPI:
        self.app = FastAPI(
            title=self.title,
            version=self.version,
            root_path=self.openapi_prefix,
            openapi_url=self.openapi_url,
            docs_url=self.docs_url,
            lifespan=lifespan,
        )
        self.configure_cors()
        self.mount_static_dirs()
        self.configure_swagger_ui()
        return self.app

    def configure_cors(self) -> None:
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def mount_static_dirs(self) -> None:
        for static_dir in self.static_dirs:
            # Serve the directory at the same path it's named
            self.app.mount(
                f"/{os.path.basename(static_dir)}",
                StaticFiles(directory=static_dir),
                name="static",
            )

    def configure_swagger_ui(self) -> None:
        if all(
            [
                self.assets_url,
                self.swagger_css_url,
                self.swagger_js_url,
                self.swagger_favicon_url,
            ]
        ):
            asset_path = fastapi_offline_swagger_ui.__path__[0]

            css_file_path = os.path.join(asset_path, "swagger-ui.css")
            js_file_path = os.path.join(asset_path, "swagger-ui-bundle.js")

            if os.path.exists(css_file_path) and os.path.exists(js_file_path):
                # Mount the local Swagger UI asset files
                self.app.mount(self.assets_url, StaticFiles(directory=asset_path), name="assets")

                # Monkey patch FastAPI's Swagger UI to use the offline assets
                applications.get_swagger_ui_html = self._swagger_monkey_patch

    def _swagger_monkey_patch(self, *args, **kwargs) -> HTMLResponse:
        return get_swagger_ui_html(
            *args,
            **kwargs,
            swagger_favicon_url=self.swagger_favicon_url,
            swagger_css_url=self.swagger_css_url,
            swagger_js_url=self.swagger_js_url,
        )
