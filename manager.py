from PyQt5 import QtWidgets, QtGui, QtCore
import requests
import os
import urllib.parse
import json
import sys
import hashlib
import logging

# Set up logging
log_folder = os.path.join(os.path.dirname(__file__), 'log')
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
logging.basicConfig(filename=os.path.join(log_folder, 'flash_game_manager.log'), level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Color Variables
BACKGROUND_COLOR = "#f0f0f0"
BUTTON_COLOR = "#4CAF50"
BUTTON_TEXT_COLOR = "white"
DETAILS_BUTTON_COLOR = "#2196F3"
REMOVE_BUTTON_COLOR = "#f44336"
TEXT_COLOR = "#333333"
SECONDARY_TEXT_COLOR = "#555555"
WIDGET_BACKGROUND_COLOR = "#ffffff"
BORDER_COLOR = "#d3d3d3"
SCROLLBAR_COLOR = "#888888"
INNER_FLASH_TAG_COLOR = "#D68B00"
OUTER_FLASH_TAG_COLOR = "#FFE5B1"
INNER_HTML5_TAG_COLOR = "#009ACD"
OUTER_HTML5_TAG_COLOR = "#B0E0E6"
INNER_OTHER_TAG_COLOR = "#555555"
OUTER_OTHER_TAG_COLOR = "#CCCCCC"
ICON_IMAGE_WIDTH = 200
ICON_IMAGE_HEIGHT = 200
SCREENSHOT_IMAGE_WIDTH = 400
SCREENSHOT_IMAGE_HEIGHT = 200
DESCRIPTION_CUTOFF = 300


class FlashGameManager(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Initializing FlashGameManager")
        self.setWindowTitle("Flash Game Manager")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        self.games_data = []
        self.my_games = []
        self.current_game = None
        self.data_folder = os.path.join(os.path.dirname(__file__), 'game_data')
        self.cache_folder = os.path.join(self.data_folder, 'cache')
        self.my_games_file = os.path.join(self.data_folder, 'my_games.json')

        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            logging.info(f"Created data folder: {self.data_folder}")
        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)
            logging.info(f"Created cache folder: {self.cache_folder}")

        self.load_my_games()
        self.init_ui()
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setStyleSheet("background-color: none;")
        self.setStatusBar(self.status_bar)

    def init_ui(self):
        logging.info("Initializing UI")
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Create tab widget for different views
        self.tabs = QtWidgets.QTabWidget()
        self.layout.addWidget(self.tabs)

        # Search View
        self.search_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.search_tab, "Search Games")
        self.create_search_view()

        # My Games View
        self.my_games_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.my_games_tab, "My Games")
        self.create_my_games_view()

        # Details View
        self.details_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.details_tab, "Game Details")
        self.create_details_view()

    def create_search_view(self):
        logging.info("Creating search view")
        search_layout = QtWidgets.QVBoxLayout(self.search_tab)

        # Search bar
        search_bar_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search for a game...")
        self.search_input.setStyleSheet("padding: 8px; font-size: 14px;")
        self.search_input.returnPressed.connect(self.search_game)
        search_button = QtWidgets.QPushButton("Search")
        search_button.setStyleSheet(f"background-color: {BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 8px; font-size: 14px; border-radius: 4px;")
        search_button.clicked.connect(self.search_game)

        search_bar_layout.addWidget(self.search_input)
        search_bar_layout.addWidget(search_button)
        search_layout.addLayout(search_bar_layout)

        # Search results area with scroll
        self.results_area = QtWidgets.QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_area.setStyleSheet("QScrollBar:vertical { width: 8px; background: #f0f0f0; } QScrollBar::handle:vertical { background: #888888; border-radius: 4px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")
        self.results_widget = QtWidgets.QWidget()
        self.results_layout = QtWidgets.QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(QtCore.Qt.AlignTop)
        self.results_area.setWidget(self.results_widget)
        self.results_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        search_layout.addWidget(self.results_area)

    def create_my_games_view(self):
        logging.info("Creating My Games view")
        my_games_layout = QtWidgets.QVBoxLayout(self.my_games_tab)

        # Filter bar
        filter_bar_layout = QtWidgets.QHBoxLayout()
        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.setPlaceholderText("Filter games...")
        self.filter_input.setStyleSheet("padding: 8px; font-size: 14px;")
        self.filter_input.returnPressed.connect(self.update_my_games_view)
        filter_button = QtWidgets.QPushButton("Filter")
        filter_button.setStyleSheet(f"background-color: {BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 8px; font-size: 14px; border-radius: 4px;")
        filter_button.clicked.connect(self.update_my_games_view)

        filter_bar_layout.addWidget(self.filter_input)
        filter_bar_layout.addWidget(filter_button)
        my_games_layout.addLayout(filter_bar_layout)

        # My games area with scroll
        self.my_games_area = QtWidgets.QScrollArea()
        self.my_games_area.setWidgetResizable(True)
        self.my_games_area.setStyleSheet("QScrollBar:vertical { width: 8px; background: #f0f0f0; } QScrollBar::handle:vertical { background: #888888; border-radius: 4px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")
        self.my_games_widget = QtWidgets.QWidget()
        self.my_games_layout = QtWidgets.QVBoxLayout(self.my_games_widget)
        self.my_games_layout.setAlignment(QtCore.Qt.AlignTop)
        self.my_games_area.setWidget(self.my_games_widget)

        my_games_layout.addWidget(self.my_games_area)
        self.update_my_games_view()

    def create_details_view(self):
        logging.info("Creating Details view")
        self.details_layout = QtWidgets.QVBoxLayout(self.details_tab)

        # Image frame
        self.image_frame = QtWidgets.QFrame()
        self.image_layout = QtWidgets.QHBoxLayout(self.image_frame)
        self.image_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.image_layout.setSpacing(20)
        self.image_frame.setStyleSheet("padding: 20px;")
        self.details_layout.addWidget(self.image_frame)

        # Game details area
        self.details_text = QtWidgets.QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet(f"background-color: {WIDGET_BACKGROUND_COLOR}; padding: 10px; border: 1px solid {BORDER_COLOR}; font-size: 14px;")
        self.details_text.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.details_text.setStyleSheet("QScrollBar:vertical { width: 8px; background: #f0f0f0; } QScrollBar::handle:vertical { background: #888888; border-radius: 4px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")
        self.details_layout.addWidget(self.details_text, stretch=2)

        # Additional info frame
        self.additional_info_text = QtWidgets.QTextEdit()
        self.additional_info_text.setReadOnly(True)
        self.additional_info_text.setStyleSheet(f"background-color: {WIDGET_BACKGROUND_COLOR}; padding: 10px; border: 1px solid {BORDER_COLOR}; font-size: 14px;")
        self.additional_info_text.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.additional_info_text.setStyleSheet("QScrollBar:vertical { width: 8px; background: #f0f0f0; } QScrollBar::handle:vertical { background: #888888; border-radius: 4px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")
        self.details_layout.addWidget(self.additional_info_text, stretch=1)

        # Add to My Games button
        self.add_to_my_games_button = QtWidgets.QPushButton("Add to My Games")
        self.add_to_my_games_button.setStyleSheet(f"background-color: {DETAILS_BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 10px; font-size: 14px; border-radius: 4px;")
        self.add_to_my_games_button.clicked.connect(self.add_current_game_to_my_games)
        self.details_layout.addWidget(self.add_to_my_games_button)

        # Close button
        close_button = QtWidgets.QPushButton("Close")
        close_button.setStyleSheet(f"background-color: {REMOVE_BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 10px; font-size: 14px; border-radius: 4px;")
        close_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.details_layout.addWidget(close_button)

    def cache_request(self, url):
        logging.info(f"Cache request for URL: {url}")
        # Create a hash of the URL to use as the cache filename
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_path = os.path.join(self.cache_folder, f"{cache_key}.json")

        # Check if the response is already cached
        if os.path.exists(cache_path):
            logging.info(f"Loading cached response for URL: {url}")
            with open(cache_path, 'r') as cache_file:
                return json.load(cache_file)

        # If not cached, make the request and cache the response
        response = requests.get(url)
        if response.status_code == 200:
            logging.info(f"Caching response for URL: {url}")
            with open(cache_path, 'w') as cache_file:
                json.dump(response.json(), cache_file)
            return response.json()
        else:
            logging.error(f"Failed to fetch data from URL: {url} with status code {response.status_code}")
            return None

    def search_game(self):
        query = self.search_input.text().strip()
        logging.info(f"Searching for game with query: {query}")
        if not query:
            logging.warning("Search input is empty")
            self.set_status_warning("Search input is empty.", 3000)
            return

        encoded_query = urllib.parse.quote(query)
        search_url = f"https://db-api.unstable.life/search?smartSearch={encoded_query}&filter=true&fields=id,title,developer,publisher,platform,library,tags,originalDescription,dateAdded,dateModified"
        self.games_data = self.cache_request(search_url)

        if self.games_data is not None:
            if len(self.games_data) == 1:
                self.games_data.append({"id": "fake_entry", "title": "", "originalDescription": ""})  # Adding a placeholder to avoid the single entry issue
            self.display_search_results()
        else:
            logging.error("Failed to fetch search results")
            self.set_status_error("Failed to fetch search results.", 3000)

    def display_search_results(self):
        logging.info("Displaying search results")
        # Clear previous search results
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Display each game in search results
        for game in self.games_data:
            game_frame = QtWidgets.QFrame()
            game_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            game_frame.setStyleSheet(f"background-color: {WIDGET_BACKGROUND_COLOR}; border: 1px solid {BORDER_COLOR}; padding: 10px; border-radius: 8px;")
            game_layout = QtWidgets.QHBoxLayout(game_frame)

            image_layout = QtWidgets.QVBoxLayout()

            # Fetch and display image
            game_id = game['id']
            if game_id == "fake_entry":
                continue

            img_label, successfully_loaded_img_label = self.load_icon_from_url_and_get_img_label(game_id)
            
            image_layout.addWidget(img_label)
            self.addPlatformTagToLayout(game, image_layout)
            game_layout.addLayout(image_layout)

            # Game info
            info_layout = QtWidgets.QVBoxLayout()

            self.addTitleLayout(game, info_layout)
            self.addDescription(game, info_layout)

            # Buttons
            details_button = QtWidgets.QPushButton("Details")
            details_button.setStyleSheet(f"background-color: {DETAILS_BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 8px; font-size: 14px; border-radius: 4px;")
            details_button.clicked.connect(lambda checked, g=game: self.show_game_details(g))
            bottom_buttons = []
            bottom_buttons.append(details_button)

            if game in self.my_games:
                remove_button = QtWidgets.QPushButton("Remove")
                remove_button.setStyleSheet(f"background-color: {REMOVE_BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 8px; font-size: 14px; border-radius: 4px;")
                remove_button.clicked.connect(lambda checked, g=game: self.remove_from_my_games(g))
                bottom_buttons.append(remove_button)
            else:
                add_button = QtWidgets.QPushButton("Add to My Games")
                add_button.setStyleSheet(f"background-color: {BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 8px; font-size: 14px; border-radius: 4px;")
                add_button.clicked.connect(lambda checked, g=game: self.add_to_my_games(g))
                bottom_buttons.append(add_button)

            self.add_bottom_aligned_buttons(info_layout, bottom_buttons, QtCore.Qt.AlignRight)


            game_layout.addLayout(info_layout)
            self.results_layout.addWidget(game_frame)

    def load_icon_from_url_and_get_img_label(self, game_id) -> tuple[QtWidgets.QLabel, bool]:
        img_url = f"https://infinity.unstable.life/images/Logos/{game_id[:2]}/{game_id[2:4]}/{game_id}.png?type=jpg"
        img_path = os.path.join(self.data_folder, f"{game_id}.png")
        if not os.path.exists(img_path):
            try:
                logging.info(f"Fetching image from URL: {img_url}")
                img_data = requests.get(img_url).content
                with open(img_path, 'wb') as f:
                    f.write(img_data)
            except Exception as e:
                logging.error(f"Error loading image from URL: {img_url} - {e}")
                img_label = QtWidgets.QLabel("No Image")
                img_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
                img_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
                return img_label, False

        pixmap = QtGui.QPixmap(img_path).scaled(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        img_label = QtWidgets.QLabel()
        img_label.setPixmap(pixmap)
        img_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
        img_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        return img_label, True

    def show_game_details(self, game):
        logging.info(f"Showing details for game: {game['title']}")
        self.tabs.setCurrentWidget(self.details_tab)
        self.current_game = game

        # Display game details with bolded keys for better readability
        details = ""
        for key, value in game.items():
            if isinstance(value, list):
                value = ', '.join(value)
            details += f"<b>{key.capitalize()}:</b> {value.replace('\n', '<br>')}<br>"
        self.details_text.setHtml(details)

        # Clear previous images in the details view
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Display logo and screenshot images
        game_id = game['id']

        # Game logo
        img_path = os.path.join(self.data_folder, f"{game_id}.png")
        if os.path.exists(img_path):
            pixmap = QtGui.QPixmap(img_path).scaled(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            logo_label = QtWidgets.QLabel()
            logo_label.setPixmap(pixmap)
            logo_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
            logo_label.setStyleSheet(f"border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
            self.image_layout.addWidget(logo_label)

        # Game screenshot
        screenshot_url = f"https://infinity.unstable.life/images/Screenshots/{game_id[:2]}/{game_id[2:4]}/{game_id}.png?type=jpg"
        screenshot_path = os.path.join(self.data_folder, f"{game_id}_screenshot.png")
        if not os.path.exists(screenshot_path):
            try:
                logging.info(f"Fetching screenshot from URL: {screenshot_url}")
                screenshot_data = requests.get(screenshot_url).content
                with open(screenshot_path, 'wb') as f:
                    f.write(screenshot_data)
            except Exception as e:
                logging.error(f"Error loading screenshot from URL: {screenshot_url} - {e}")
                return

        screenshot_pixmap = QtGui.QPixmap(screenshot_path).scaled(SCREENSHOT_IMAGE_WIDTH, SCREENSHOT_IMAGE_HEIGHT, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        screenshot_label = QtWidgets.QLabel()
        screenshot_label.setPixmap(screenshot_pixmap)
        screenshot_label.setFixedSize(SCREENSHOT_IMAGE_WIDTH, SCREENSHOT_IMAGE_HEIGHT)
        screenshot_label.setStyleSheet(f"border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
        self.image_layout.addWidget(screenshot_label)

        # Fetch and display additional game information
        addapps_url = f"https://db-api.unstable.life/addapps?id={game_id}"
        additional_apps = self.cache_request(addapps_url)
        if additional_apps is not None:
            additional_info = "<b>Additional Applications:</b><br>"
            for app in additional_apps:
                additional_info += f"<b>Name:</b> {app.get('name', 'N/A')}<br>"
                additional_info += f"<b>Application Path:</b> {app.get('applicationPath', 'N/A')}<br>"
                additional_info += f"<b>Launch Command:</b> {app.get('launchCommand', 'N/A')}<br><br>"
            self.additional_info_text.setHtml(additional_info)
        else:
            self.additional_info_text.setHtml("<b>Additional Applications:</b> None found.")

        # Show or hide the Add to My Games button
        if game in self.my_games:
            self.add_to_my_games_button.hide()
        else:
            self.add_to_my_games_button.show()

    def add_current_game_to_my_games(self):
        if self.current_game is None:
            logging.warning("No game is currently selected to add to My Games")
            QtWidgets.QMessageBox.warning(self, "No Game Selected", "No game is currently open to add to My Games.")
            return
        self.add_to_my_games(self.current_game)

    def add_to_my_games(self, game):
        logging.info(f"Adding game to My Games: {game['title']}")
        if game not in self.my_games:
            self.my_games.append(game)
            self.update_my_games_view()
            self.save_my_games()

            # Cache the screenshot in advance for offline use
            game_id = game['id']
            screenshot_url = f"https://infinity.unstable.life/images/Screenshots/{game_id[:2]}/{game_id[2:4]}/{game_id}.png?type=jpg"
            screenshot_path = os.path.join(self.data_folder, f"{game_id}_screenshot.png")
            if not os.path.exists(screenshot_path):
                try:
                    logging.info(f"Caching screenshot for game: {game['title']}")
                    screenshot_data = requests.get(screenshot_url).content
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot_data)
                except Exception as e:
                    logging.error(f"Error caching screenshot for game: {game['title']} - {e}")

            self.set_status_success("Game added to your collection.", 3000)
        else:
            logging.info(f"Game already in My Games: {game['title']}")
            self.set_status_warning("This game is already in your collection.", 3000)
        # Update search view to reflect the change
        self.display_search_results()

    def update_my_games_view(self):
        logging.info("Updating My Games view")
        # Clear previous my games results
        for i in reversed(range(self.my_games_layout.count())):
            widget = self.my_games_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Display each game in my games
        filter_text = self.filter_input.text().strip().lower()
        logging.info(f"Filtering My Games with filter text: {filter_text}")

        for game in self.my_games:
            if filter_text and filter_text not in game['title'].lower():
                continue

            game_frame = QtWidgets.QFrame()
            game_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            game_frame.setStyleSheet(f"background-color: {WIDGET_BACKGROUND_COLOR}; border: 1px solid {BORDER_COLOR}; padding: 10px; border-radius: 8px;")
            game_layout = QtWidgets.QHBoxLayout(game_frame)

            image_layout = QtWidgets.QVBoxLayout()

            # Fetch and display image
            game_id = game['id']
            img_path = os.path.join(self.data_folder, f"{game_id}.png")
            if os.path.exists(img_path):
                pixmap = QtGui.QPixmap(img_path).scaled(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                img_label = QtWidgets.QLabel()
                img_label.setPixmap(pixmap)
                img_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
                img_label.setStyleSheet(f"border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
                img_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
                image_layout.addWidget(img_label)
            else:
                img_label = QtWidgets.QLabel("No Image")
                img_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
                img_label.setStyleSheet(f"border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
                img_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
                image_layout.addWidget(img_label)
            self.addPlatformTagToLayout(game, image_layout)
            game_layout.addLayout(image_layout)

            # Game info
            info_layout = QtWidgets.QVBoxLayout()
            
            self.addTitleLayout(game, info_layout)
            self.addDescription(game, info_layout)

            # Buttons
            details_button = QtWidgets.QPushButton("Details")
            details_button.setStyleSheet(f"background-color: {DETAILS_BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 8px; font-size: 14px; border-radius: 4px;")
            details_button.clicked.connect(lambda checked, g=game: self.show_game_details(g))

            remove_button = QtWidgets.QPushButton("Remove")
            remove_button.setStyleSheet(f"background-color: {REMOVE_BUTTON_COLOR}; color: {BUTTON_TEXT_COLOR}; padding: 8px; font-size: 14px; border-radius: 4px;")
            remove_button.clicked.connect(lambda checked, g=game: self.remove_from_my_games(g))

            self.add_bottom_aligned_buttons(info_layout, [details_button, remove_button], QtCore.Qt.AlignRight)

            game_layout.addLayout(info_layout)
            self.my_games_layout.addWidget(game_frame)

    def addTitleLayout(self, game, info_layout: QtWidgets.QVBoxLayout):
        title_label = QtWidgets.QLabel(f"{game['title']}")
        title_label.setFont(QtGui.QFont("Helvetica", 14, QtGui.QFont.Bold))
        title_label.setStyleSheet(f"color: {TEXT_COLOR};")
        info_layout.addWidget(title_label)

    def addDescription(self, game, info_layout: QtWidgets.QBoxLayout):
        if 'originalDescription' in game:
                description = game['originalDescription']
                if len(description) > DESCRIPTION_CUTOFF:
                    description = description[:DESCRIPTION_CUTOFF] + "..."
                description_label = QtWidgets.QLabel(description)
                description_label.setWordWrap(True)
                description_label.setStyleSheet(f"color: {SECONDARY_TEXT_COLOR};")
                description_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
                info_layout.addWidget(description_label)

    def addPlatformTagToLayout(self, game, layout: QtWidgets.QBoxLayout):
        if 'platform' in game:
            platform_name = game['platform']
            if platform_name.lower() == 'flash':
                platform_inner_color = INNER_FLASH_TAG_COLOR
                platform_outer_color = OUTER_FLASH_TAG_COLOR
            elif platform_name.lower() == 'html5':
                platform_inner_color = INNER_HTML5_TAG_COLOR
                platform_outer_color = OUTER_HTML5_TAG_COLOR
            else:
                platform_inner_color = INNER_OTHER_TAG_COLOR
                platform_outer_color = OUTER_OTHER_TAG_COLOR

            platform_label = QtWidgets.QLabel(f"{platform_name}")
            platform_label.setStyleSheet(f"""
                color: {platform_inner_color};
                background-color: {platform_outer_color};
                font-size: 16px;
                padding: 4px 8px;  /* Reduced padding to minimize width */
                border-radius: 4px;
                max-height: 18px;
            """)
            platform_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)  # Force the platform label to be minimal
            platform_label.setAlignment(QtCore.Qt.AlignCenter)  # Center-align text inside the label
            layout.addWidget(platform_label, alignment=QtCore.Qt.AlignBottom)

    def add_bottom_aligned_buttons(self, input_layout: QtWidgets.QBoxLayout, input_buttons: list[QtWidgets.QPushButton], horizontalAlignment: QtCore.Qt.AlignmentFlag):
        horizontal_layout = QtWidgets.QHBoxLayout()
        for button in input_buttons:
            horizontal_layout.addWidget(button, horizontalAlignment)
        horizontal_layout.setAlignment(QtCore.Qt.AlignBottom)
        input_layout.addLayout(horizontal_layout)

    def remove_from_my_games(self, game):
        logging.info(f"Removing game from My Games: {game['title']}")
        self.my_games.remove(game)
        self.update_my_games_view()
        self.save_my_games()
        self.set_status_success("Game removed from your collection.", 3000)
        # Update search view to reflect the change
        self.display_search_results()

    def save_my_games(self):
        logging.info("Saving My Games to file")
        with open(self.my_games_file, 'w') as f:
            json.dump(self.my_games, f, indent=4)

    def load_my_games(self):
        logging.info("Loading My Games from file")
        if os.path.exists(self.my_games_file):
            with open(self.my_games_file, 'r') as f:
                self.my_games = json.load(f)

    def set_status_warning(self, input: str, time: int):
        self.status_bar.setStyleSheet("background-color: yellow; color: black;")
        QtCore.QTimer.singleShot(time, lambda: self.status_bar.setStyleSheet(""))
        self.status_bar.showMessage(input, time)

    def set_status_error(self, input: str, time: int):
        self.status_bar.setStyleSheet("background-color: red; color: white;")
        QtCore.QTimer.singleShot(time, lambda: self.status_bar.setStyleSheet(""))
        self.status_bar.showMessage(input, time)

    def set_status_success(self, input: str, time: int):
        self.status_bar.setStyleSheet("background-color: lightgreen; color: black;")
        QtCore.QTimer.singleShot(time, lambda: self.status_bar.setStyleSheet(""))
        self.status_bar.showMessage(input, time)

if __name__ == "__main__":
    logging.info("Starting FlashGameManager application")
    app = QtWidgets.QApplication(sys.argv)
    window = FlashGameManager()
    window.show()
    sys.exit(app.exec_())
