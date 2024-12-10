# junos
[Home Assistant](https://www.home-assistant.io/) component for monitoring and (eventually) controlling [Juniper](https://juniper.net) Junos OS devices.  So far it has been tested on an EX4300 switch, but should work on any other switches and routers running the Junos OS.

Now welcoming feedback for features and bugs.  This was mostly taken from my Daikin Skyport integration code and modified.

## Installation

This component can be installed via the [Home Assistant Community Store (HACS)](https://hacs.xyz/) or manually.

This integration now requires Home Assistant version 2024.02 or later due to changes made in that version that are not backward compatible.

### Install via HACS

_HACS must be [installed](https://hacs.xyz/docs/installation/prerequisites) before following these steps._

1. Log into your Home Assistant instance and open HACS via the sidebar on the left
2. In the HACS menu, open **Integrations**
3. On the integrations page, select the "vertical dots" icon in the top-right corner, and select **Custom respositories**
4. Paste `https://github.com/apetrycki/junos` into the **Repository** field and select **Integration** in the **Category** menu
5. Click **ADD**
6. Click **+ EXPLORE & DOWNLOAD REPOSITORIES**
7. Select **Junos OS** and click the **DOWNLOAD** button
8. Click **DOWNLOAD**
9. Restart Home Assistant Core via the Home Assistant console by navigating to **Settings** in the sidebar on the left, selecting **System**, clicking the **Power** button in the top right, and **Restart Home Assistant**. A restart is necessary in order to load the component.

### Manual Install

_A manual installation is more risky than installation via HACS. You must be familiar with how to SSH into Home Assistant and working in the Linux shell to perform these steps._

1. Download or clone the component's repository by selecting the **Code** button on the [component's GitHub page](https://github.com/apetrycki/junos).
2. If you downloaded the component as a zip file, extract the file.
3. Copy the `custom_components/junos` folder from the repository to your Home Assistant `custom_components` folder. Once done, the full path to the component in Home Assistant should be `/config/custom_components/junos`. The `__init__.py` file (along with the rest of the files) should be directly in the `junos` folder.

## Usage

In order for this component to talk to your Junos device, you need to configure the [REST](https://www.juniper.net/documentation/us/en/software/junos/rest-api/topics/example/rest-api-configuring-example.html) interface.

Once completed, make note of which protocol (HTTP or HTTPS), the IP or hostname, and the port you configured.  If it's HTTPS, you'll also need to either add your root CA to Home Assistant (through Additional CA integration for example) or disable verification in this integration.

Also make sure you have a user and password that is allowed to use the REST interface.

Once Home Assistant has restarted, navigate to **Settings** in the sidebar, then **Devices & services**. Click **+ Add Integration** at the bottom right.  Use the search box to search for 'Junos OS'.

