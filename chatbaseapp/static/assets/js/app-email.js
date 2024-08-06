/**
 * App Email
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {
  (function () {
    const emailList = document.querySelector('.email-list'),
      emailListItems = [].slice.call(document.querySelectorAll('.email-list-item')),
      emailListItemInputs = [].slice.call(document.querySelectorAll('.email-list-item-input')),
      emailView = document.querySelector('.app-email-view-content'),
      emailFilters = document.querySelector('.email-filters'),
      emailFilterByFolders = [].slice.call(document.querySelectorAll('.email-filter-folders li')),
      emailEditor = document.querySelector('.email-editor'),
      appEmailSidebar = document.querySelector('.app-email-sidebar'),
      appOverlay = document.querySelector('.app-overlay'),
      emailReplyEditor = document.querySelector('.email-reply-editor'),
      bookmarkEmail = [].slice.call(document.querySelectorAll('.email-list-item-bookmark')),
      selectAllEmails = document.getElementById('email-select-all'),
      toggleCC = document.querySelector('.email-compose-toggle-cc'),
      toggleBCC = document.querySelector('.email-compose-toggle-bcc'),
      // emailCompose = document.querySelector('.app-email-compose'),
      emailListDelete = document.querySelector('.email-list-delete'),
      emailListRead = document.querySelector('.email-list-read'),
      refreshEmails = document.querySelector('.email-refresh'),
      // emailViewContainer = document.getElementById('app-email-view'),
      emailFilterFolderLists = [].slice.call(document.querySelectorAll('.email-filter-folders li')),
      emailListItemActions = [].slice.call(document.querySelectorAll('.email-list-item-actions li')),
      attachfileInput = document.querySelector('#attach-file'),
      submitBtn = document.querySelector('#submitButton'),
      uploadFileList = document.querySelector('#file-list')

      console.log(emailListItemActions);

    


    // Initialize PerfectScrollbar
    // ------------------------------
    // Email list scrollbar
    if (emailList) {
      let emailListInstance = new PerfectScrollbar(emailList, {
        wheelPropagation: false,
        suppressScrollX: true
      });
    }

    // Sidebar tags scrollbar
    if (emailFilters) {
      new PerfectScrollbar(emailFilters, {
        wheelPropagation: false,
        suppressScrollX: true
      });
    }

    // Email view scrollbar
    if (emailView) {
      new PerfectScrollbar(emailView, {
        wheelPropagation: false,
        suppressScrollX: true
      });
    }



    // Select all
    if (selectAllEmails) {
      selectAllEmails.addEventListener('click', e => {
        if (e.currentTarget.checked) {
          emailListItemInputs.forEach(c => (c.checked = 1));
        } else {
          emailListItemInputs.forEach(c => (c.checked = 0));
        }
      });
    }

    // Select single email
    if (emailListItemInputs) {
      emailListItemInputs.forEach(emailListItemInput => {
        emailListItemInput.addEventListener('click', e => {
          e.stopPropagation();
          // Check input count to reset the indeterminate state
          let emailListItemInputCount = 0;
          emailListItemInputs.forEach(emailListItemInput => {
            if (emailListItemInput.checked) {
              emailListItemInputCount++;
            }
          });

          if (emailListItemInputCount < emailListItemInputs.length) {
            if (emailListItemInputCount == 0) {
              selectAllEmails.indeterminate = false;
            } else {
              selectAllEmails.indeterminate = true;
            }
          } else {
            if (emailListItemInputCount == emailListItemInputs.length) {
              selectAllEmails.indeterminate = false;
              selectAllEmails.checked = true;
            } else {
              selectAllEmails.indeterminate = false;
            }
          }
        });
      });
    }

    // Empty compose email message inputs when modal is hidden
    // emailCompose.addEventListener('hidden.bs.modal', event => {
    //   document.querySelector('.email-editor .ql-editor').innerHTML = '';
    //   $('#emailContacts').val('');
    //   initSelect2();
    // });

    // Refresh Mails

    if (refreshEmails && emailList) {
      let emailListJq = $('.email-list'),
        emailListInstance = new PerfectScrollbar(emailList, {
          wheelPropagation: false,
          suppressScrollX: true
        });
      // ? Using jquery vars due to BlockUI jQuery dependency
      refreshEmails.addEventListener('click', e => {
        emailListJq.block({
          message: '<div class="spinner-border text-primary" role="status"></div>',
          timeout: 1000,
          css: {
            backgroundColor: 'transparent',
            border: '0'
          },
          overlayCSS: {
            backgroundColor: '#000',
            opacity: 0.1
          },
          onBlock: function () {
            emailListInstance.settings.suppressScrollY = true;
          },
          onUnblock: function () {
            emailListInstance.settings.suppressScrollY = false;
          }
        });
      });
    }

    // Earlier msgs
    // ? Using jquery vars due to jQuery animation (slideToggle) dependency
    let earlierMsg = $('.email-earlier-msgs');
    if (earlierMsg.length) {
      earlierMsg.on('click', function () {
        let $this = $(this);
        $this.parents().find('.email-card-last').addClass('hide-pseudo');
        $this.next('.email-card-prev').slideToggle();
        $this.remove();
      });
    }

    // Email contacts (select2)
    // ? Using jquery vars due to select2 jQuery dependency
    let emailContacts = $('#emailContacts');
    function initSelect2() {
      if (emailContacts.length) {
        function renderContactsAvatar(option) {
          if (!option.id) {
            return option.text;
          }
          let $avatar =
            "<div class='d-flex flex-wrap align-items-center lh-1 me-1'>" +
            "<div class='avatar avatar-xs me-2 w-px-20 h-px-20'>" +
            "<img src='" +
            assetsPath +
            'img/avatars/' +
            $(option.element).data('avatar') +
            "' alt='avatar' class='rounded-circle' />" +
            '</div>' +
            option.text +
            '</div>';

          return $avatar;
        }
        emailContacts.wrap('<div class="position-relative"></div>').select2({
          placeholder: 'Select value',
          dropdownParent: emailContacts.parent(),
          closeOnSelect: false,
          templateResult: renderContactsAvatar,
          templateSelection: renderContactsAvatar,
          escapeMarkup: function (es) {
            return es;
          }
        });
      }
    }
    initSelect2();

    // Scroll to bottom on reply click
    // ? Using jquery vars due to jQuery animation dependency
    let emailViewContent = $('.app-email-view-content');
    emailViewContent.find('.scroll-to-reply').on('click', function () {
      if (emailViewContent[0].scrollTop === 0) {
        emailViewContent.animate(
          {
            scrollTop: emailViewContent[0].scrollHeight
          },
          1500
        );
      }
    });

    // Delete multiple email
    if (emailListDelete) {
      emailListDelete.addEventListener('click', e => {
        let ids = []
        emailListItemInputs.map(emailListItemInput => {
          if (emailListItemInput.checked) {
            ids.push(emailListItemInput.id);
          }
        });
        selectAllEmails.indeterminate = false;
        selectAllEmails.checked = false;
        if(ids.length === 0) return
        let body = {id: ids.join(',')}
        let formData = new FormData();
        formData.append('id', ids.join(','))
        fetch('/delete_document', {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: formData,
        })
          .then(response => response.json())
          .then(data => {
            console.log(data); // File deleted successfully
            location.reload();
          })
          .catch(error => console.error(error)); // Error occurred during file delete
      });
    }

    // Email List Items Actions
    if (emailListItemActions) {
      emailListItemActions.forEach(emailListItemAction => {
        emailListItemAction.addEventListener('click', e => {
          e.stopPropagation();
          let currentTarget = e.currentTarget;
          let formData = new FormData();
          formData.append('id', currentTarget.id)
          if (Helpers._hasClass('email-delete', currentTarget)) {
            fetch('/delete_document', {
              method: 'POST',
              headers: {
                'X-CSRFToken': getCookie('csrftoken')
              },
              body: formData
            })
              .then(response => response.json())
              .then(data => {
                console.log(data); // File deleted successfully
                location.reload();
              })
              .catch(error => console.error(error)); // Error occurred during file delete
          };
        });
      });
    };
  })();
});



