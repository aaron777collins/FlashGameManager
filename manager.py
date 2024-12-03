from io import BytesIO
from threading import Thread
from PyQt5 import QtWidgets, QtGui, QtCore, QtNetwork
import requests
import os
import urllib.parse
import json
import sys
import hashlib
import logging
from appdirs import user_data_dir
from PIL import Image
import subprocess

data_dir = user_data_dir("FlashGameManager", "aaron777collins")
os.makedirs(data_dir, exist_ok=True)
data_folder = os.path.join(data_dir, 'data')
log_folder = os.path.join(data_folder, 'FlashGameManager', 'log')
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
PAGE_SIZE = 15
DEFAULT_STATUS_BAR_TIME = 3000
INFINITE_SCROLL_THRESHOLD = 0.9


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
        self.data_folder = os.path.join(data_folder, 'FlashGameManager', 'game_data')
        self.steam_tinker_launch_exec = os.path.join(self.data_folder, 'SteamTinkerLaunch', 'steamtinkerlaunch')
        self.images_folder = os.path.join(self.data_folder, 'images')
        self.cache_folder = os.path.join(self.data_folder, 'cache')
        self.my_games_file = os.path.join(self.data_folder, 'my_games.json')
        self.game_image_layouts_dict: dict[str, QtWidgets.QLayout] = {}

        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            logging.info(f"Created data folder: {self.data_folder}")
        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)
            logging.info(f"Created cache folder: {self.cache_folder}")

        self.window_icon_path = os.path.join(self.images_folder, 'icon_128x128.png')
        logging.info(f"Loading window icon from {self.window_icon_path}")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.window_icon_path), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.setWindowIcon(icon)
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

    def add_current_game_to_my_games(self):
        if self.current_game is None:
            logging.warning("No game is currently selected to add to My Games")
            self.set_status_warning("No game is currently open to add to My Games.", DEFAULT_STATUS_BAR_TIME)
            return
        self.add_to_my_games(self.current_game)

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
            self.set_status_warning("Search input is empty.", DEFAULT_STATUS_BAR_TIME)
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
            self.set_status_error("Failed to fetch search results.", DEFAULT_STATUS_BAR_TIME)

    def display_search_results(self):
        logging.info("Displaying search results (initial)")

        # Clear previous search results
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Define variables for pagination
        self.current_page = 1
        self.all_games_loaded = False  # Flag to track if all games are displayed

        # Display initial set of games (modify this to fetch data for page 1)
        self.display_games_for_search_page(self.current_page)

        # Connect scroll event handler
        self.results_area.verticalScrollBar().valueChanged.connect(self.handle_scroll)

    def handle_scroll(self, value):
        # Check if scroll is near the bottom
        scroll_bar = self.results_area.verticalScrollBar()
        max_value = scroll_bar.maximum()
        threshold = INFINITE_SCROLL_THRESHOLD  # Adjust this value to define "near bottom"

        if (max_value == 0):
            self.display_games_for_search_page(0)
            return

        if (value / max_value) >= threshold and not self.all_games_loaded:
            self.display_games_for_search_page(self.current_page + 1)

    def display_games_for_search_page(self, page_number):
        logging.info(f"Getting search results for page {page_number}")
        # Fetch data for the given page
        fetched_games = self.get_games_by_page(page_number)

        if not fetched_games:
            self.all_games_loaded = True
            return

        self.current_page += 1

        # Display each game in fetched data
        for game in fetched_games:
            game_frame = QtWidgets.QFrame()
            game_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            game_frame.setStyleSheet(f"background-color: {WIDGET_BACKGROUND_COLOR}; border: 1px solid {BORDER_COLOR}; padding: 10px; border-radius: 8px;")
            game_layout = QtWidgets.QHBoxLayout(game_frame)

            image_layout = QtWidgets.QVBoxLayout()

            # Fetch and display image
            game_id = game['id']
            if game_id == "fake_entry":
                continue

            img_label = self.load_icon_from_url_and_get_img_label(game_id)

            image_layout.addWidget(img_label)
            self.game_image_layouts_dict[game_id] = image_layout
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
            # Calculate the new scroll position to maintain visibility
            new_scroll_pos = self.results_layout.count() * game_frame.height() - self.results_area.height()

            # Set the scroll position smoothly (optional)
            animation = QtCore.QPropertyAnimation(self.results_area.verticalScrollBar(), b"value")
            animation.setDuration(100)
            animation.setStartValue(self.results_area.verticalScrollBar().value())
            animation.setEndValue(new_scroll_pos)
            animation.start()
            self.results_layout.addWidget(game_frame)

        logging.info(f"Displayed search results for page {page_number}")
        self.set_status_success(f"Displayed search results for page {page_number}", DEFAULT_STATUS_BAR_TIME)

    def get_games_by_page(self, page_number: int) -> list:
        page_index = page_number-1
        start_num = page_index * PAGE_SIZE
        end_num = (page_index+1) * PAGE_SIZE
        return self.games_data[start_num:end_num]

    def load_icon_from_url_and_get_img_label(self, game_id) -> QtWidgets.QLabel:
        img_url = f"https://infinity.unstable.life/images/Logos/{game_id[:2]}/{game_id[2:4]}/{game_id}.png?type=png"
        img_path = os.path.join(self.data_folder, f"{game_id}.png")

        # Placeholder label while the image loads
        placeholder_label = QtWidgets.QLabel("Loading...")
        placeholder_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
        placeholder_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)

        # Start asynchronous image loading with ImageDownloader
        downloader = ImageDownloader(game_id, img_url, img_path)
        downloader.image_loaded.connect(self.update_image_layout)

        # Optionally store downloader instance to keep a reference if needed
        setattr(self, f"downloader_{game_id}", downloader)

        return placeholder_label

    @QtCore.pyqtSlot(str, QtWidgets.QLabel)
    def update_image_layout(self, game_id, img_label):
        if game_id in self.game_image_layouts_dict:
            layout = self.game_image_layouts_dict[game_id]
            old_widget = layout.itemAt(0).widget()
            layout.replaceWidget(old_widget, img_label)
            old_widget.deleteLater()

    def show_game_details(self, game):
        logging.info(f"Showing details for game: {game['title']}")
        self.tabs.setCurrentWidget(self.details_tab)
        self.current_game = game

        # Display game details with bolded keys for better readability
        details = ""
        for key, value in game.items():
            if isinstance(value, list):
                value = ', '.join(value)
            details += "<b>" + key.capitalize() + ":</b>" + value.replace('\n', '<br>') + "<br>"
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
        screenshot_url = f"https://infinity.unstable.life/images/Screenshots/{game_id[:2]}/{game_id[2:4]}/{game_id}.png?type=png"
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

    def add_to_my_games(self, game):
        logging.info(f"Adding game to My Games: {game['title']}")
        if game not in self.my_games:
            self.my_games.append(game)
            self.update_my_games_view()
            self.save_my_games()

            # Cache the screenshot in advance for offline use
            game_id = game['id']
            screenshot_url = f"https://infinity.unstable.life/images/Screenshots/{game_id[:2]}/{game_id[2:4]}/{game_id}.png?type=png"
            screenshot_path = os.path.join(self.data_folder, f"{game_id}_screenshot.png")
            if not os.path.exists(screenshot_path):
                try:
                    logging.info(f"Caching screenshot for game: {game['title']}")
                    screenshot_data = requests.get(screenshot_url).content
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot_data)
                except Exception as e:
                    logging.error(f"Error caching screenshot for game: {game['title']} - {e}")

            # Set paths and commands compatible with Flatpak
            flashpoint_dir = os.path.join(self.data_folder, "flashpoint-nano")
            flash_nano = os.path.join(flashpoint_dir, "flashpoint.sh")

            # Prepare the SteamTinkerLaunch command with adjusted paths
            steamtinkerlaunch_command = [
                self.steam_tinker_launch_exec, "addnonsteamgame",
                f"--appname={game['title']}",
                f"--exepath=\"{flash_nano}\"",
                f"--launchoptions=\"{game_id}\"",
                f"--iconpath={os.path.join(self.data_folder, f'{game_id}.png')}"
            ]

            # Debug: Print the constructed command
            logging.debug("SteamTinkerLaunch Command: " + " ".join(steamtinkerlaunch_command))

            # Execute the command if permissions allow
            try:
                result = subprocess.run(steamtinkerlaunch_command, capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info(f"The game {game['title']} was added to Steam.")
                    self.set_status_success("Game added to your collection.", DEFAULT_STATUS_BAR_TIME)
                else:
                    logging.error(
                        f"Failed to add game with SteamTinkerLaunch. "
                        f"Command output: {result.stdout}, Command error: {result.stderr}"
                    )
                    self.set_status_error("Error adding game to collection.", DEFAULT_STATUS_BAR_TIME)
            except Exception as e:
                logging.error(f"Error executing SteamTinkerLaunch command: {e}")
                self.set_status_error("Failed to add game due to execution error.", DEFAULT_STATUS_BAR_TIME)
        else:
            logging.info(f"Game already in My Games: {game['title']}")
            self.set_status_warning("This game is already in your collection.", DEFAULT_STATUS_BAR_TIME)

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

            # Fetch and display image using ImageDownloader
            game_id = game['id']
            img_path = os.path.join(self.data_folder, f"{game_id}.png")
            if os.path.exists(img_path):
                # Load the image if it exists locally
                img_label = self.load_image_synchronously(game_id, img_path, ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
                image_layout.addWidget(img_label)
            else:
                # Create placeholder and download image asynchronously
                img_label = QtWidgets.QLabel("Loading...")
                img_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
                img_label.setStyleSheet(f"border: 1px solid {BORDER_COLOR}; border-radius: 8px;")
                img_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
                image_layout.addWidget(img_label)

                img_url = f"https://infinity.unstable.life/images/Logos/{game_id[:2]}/{game_id[2:4]}/{game_id}.png?type=png"
                downloader = ImageDownloader(game_id, img_url, img_path)
                downloader.image_loaded.connect(self.update_image_layout)
                setattr(self, f"downloader_{game_id}", downloader)  # Keep reference to prevent garbage collection

            self.game_image_layouts_dict[game_id] = image_layout  # Store layout reference for updates
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
            platform_label = QtWidgets.QLabel(f"{platform_name}")
            if platform_name.lower() == 'flash':
                platform_label.setObjectName("flashTag")
                platform_label.setStyleSheet(f"background-color: {OUTER_FLASH_TAG_COLOR}")
            elif platform_name.lower() == 'html5':
                platform_label.setObjectName("html5Tag")
                platform_label.setStyleSheet(f"background-color: {OUTER_HTML5_TAG_COLOR}")
            else:
                platform_label.setObjectName("otherTag")
                platform_label.setStyleSheet(f"background-color: {OUTER_OTHER_TAG_COLOR}")
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
        self.set_status_success("Game removed from your collection.", DEFAULT_STATUS_BAR_TIME)
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

    def load_image_synchronously(self, game_id: str, img_path: str, img_width: int, img_height: int) -> QtWidgets.QLabel:
        """
        Load an image synchronously from a given path and return an QLabel with the image.
        If the image is not available or fails to load, return a QLabel with a placeholder.

        :param game_id: Unique identifier for the game
        :param img_path: Path to the image file
        :param img_width: Width of the image to display
        :param img_height: Height of the image to display
        :return: QLabel containing the loaded image or a placeholder
        """
        logging.info(f"Attempting to load image for game ID {game_id} from path: {img_path}")

        # Create QLabel for the image
        img_label = QtWidgets.QLabel()
        img_label.setFixedSize(img_width, img_height)
        img_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        img_label.setStyleSheet(f"border: 1px solid {BORDER_COLOR}; border-radius: 8px;")

        # Check if the image file exists
        if os.path.exists(img_path):
            pixmap = QtGui.QPixmap(img_path)
            if not pixmap.isNull():
                # Scale pixmap to desired size and set it on QLabel
                pixmap = pixmap.scaled(img_width, img_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                img_label.setPixmap(pixmap)
                logging.info(f"Image for game ID {game_id} loaded successfully.")
            else:
                # If pixmap is null, set placeholder text
                logging.warning(f"Image at {img_path} could not be loaded. Using placeholder.")
                img_label.setText("Error: Could not load image")
        else:
            # If image file doesn't exist, set placeholder text
            logging.warning(f"Image file does not exist at {img_path}. Using placeholder.")
            img_label.setText("No Image")

        return img_label

class ImageDownloader(QtCore.QObject):
    image_loaded = QtCore.pyqtSignal(str, QtWidgets.QLabel)  # Signal emitted when image is loaded

    def __init__(self, game_id, img_url, img_path):
        super().__init__()
        self.game_id = game_id
        self.img_url = img_url
        self.img_path = img_path
        self.network_manager = QtNetwork.QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_image_downloaded)
        self.start_download()

    def start_download(self):
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(self.img_url))
        self.network_manager.get(request)

    @QtCore.pyqtSlot(QtNetwork.QNetworkReply)
    def on_image_downloaded(self, reply: QtNetwork.QNetworkReply):
        if reply.error() == QtNetwork.QNetworkReply.NoError:
            try:
                # Read image data from the reply
                image_data = reply.readAll().data()
                logging.info(f"Image for {self.game_id} downloaded successfully")

                # Save image to file
                with open(self.img_path, 'wb') as f:
                    f.write(image_data)
                    f.flush()
                    os.fsync(f.fileno())
                logging.info(f"Image for {self.game_id} saved to {self.img_path}")

                # Load the image for display
                image = Image.open(BytesIO(image_data)).convert("RGBA")
                qt_image = QtGui.QImage(
                    image.tobytes(), image.width, image.height, QtGui.QImage.Format_RGBA8888
                )
                pixmap = QtGui.QPixmap.fromImage(qt_image)

                # Scale the QPixmap and set it on QLabel
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT,
                        QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                    )
                    img_label = QtWidgets.QLabel()
                    img_label.setPixmap(pixmap)
                    img_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
                    img_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
                    logging.info(f"Image for {self.game_id} successfully loaded into QLabel.")
                else:
                    logging.warning("Warning: Loaded QPixmap is null.")
                    img_label = self.create_error_label()
            except Exception as e:
                logging.error(f"Failed to save or load image for {self.game_id}: {e}")
                img_label = self.create_error_label()
        else:
            logging.error(f"Error downloading image for {self.game_id}: {reply.errorString()}")
            img_label = self.create_error_label()

        # Emit signal to notify main widget to update layout
        self.image_loaded.emit(self.game_id, img_label)
        reply.deleteLater()

    def create_error_label(self):
        """Create a label indicating an error in loading the image."""
        error_label = QtWidgets.QLabel("Error")
        error_label.setFixedSize(ICON_IMAGE_WIDTH, ICON_IMAGE_HEIGHT)
        error_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        return error_label

if __name__ == "__main__":
    logging.info("Starting FlashGameManager application")
    app = QtWidgets.QApplication(sys.argv)
    # Create stylesheet with variables
    app.setStyleSheet(f"""
    QWidget {{
        background-color: {BACKGROUND_COLOR};
        color: {TEXT_COLOR};
    }}
    QPushButton {{
        background-color: {BUTTON_COLOR};
        color: {BUTTON_TEXT_COLOR};
        padding: 8px;
        font-size: 14px;
        border-radius: 4px;
    }}
    QPushButton#detailsButton {{
        background-color: {DETAILS_BUTTON_COLOR};
        color: {BUTTON_TEXT_COLOR};
    }}
    QPushButton#removeButton {{
        background-color: {REMOVE_BUTTON_COLOR};
        color: {BUTTON_TEXT_COLOR};
    }}
    QLabel {{
        color: {TEXT_COLOR};
    }}
    QLineEdit {{
        background-color: white;
        color: {TEXT_COLOR};
        padding: 5px;
        border-radius: 4px;
    }}
    QScrollArea {{
        background-color: {BACKGROUND_COLOR};
    }}
    QTextEdit {{
        background-color: {WIDGET_BACKGROUND_COLOR};
        color: {TEXT_COLOR};
        padding: 10px;
        border: 1px solid {BORDER_COLOR};
    }}
    QScrollBar:vertical {{
        background: {BACKGROUND_COLOR};
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {SCROLLBAR_COLOR};
        border-radius: 4px;
    }}
    QLabel#flashTag {{
        color: {INNER_FLASH_TAG_COLOR};
        background-color: {OUTER_FLASH_TAG_COLOR};
        font-size: 16px;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QLabel#html5Tag {{
        color: {INNER_HTML5_TAG_COLOR};
        background-color: {OUTER_HTML5_TAG_COLOR};
        font-size: 16px;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QLabel#otherTag {{
        color: {INNER_OTHER_TAG_COLOR};
        background-color: {OUTER_OTHER_TAG_COLOR};
        font-size: 16px;
        padding: 4px 8px;
        border-radius: 4px;
    }}
""")
    window = FlashGameManager()
    window.show()
    sys.exit(app.exec_())
