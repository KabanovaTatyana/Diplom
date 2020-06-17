$('#file-input').focus(function () {
        $('label').addClass('focus');
    })
    .focusout(function () {
        $('label').removeClass('focus');
    });

var dropZone = $('#upload-container');

dropZone.on('drag dragstart dragend dragover dragenter dragleave drop', function () {
    return false;
});

dropZone.on('dragover dragenter', function () {
    dropZone.addClass('dragover');
});

dropZone.on('dragleave', function (e) {
    dropZone.removeClass('dragover');
});

dropZone.on('dragleave', function (e) {
    var dx = e.pageX - dropZone.offset().left;
    var dy = e.pageY - dropZone.offset().top;

    if ((dx < 0) || (dx > dropZone.width()) || (dy < 0) || (dy > dropZone.height())) {
        dropZone.removeClass('dragover');
    }
});

dropZone.on('drop', function (e) {
    dropZone.removeClass('dragover');

    var files = e.originalEvent.dataTransfer.files;

    sendFile(files);
});

$('#file-input').change(function () {
    var files = this.files;
    sendFile(files);
});

function sendFile(files) {
    dropZone.parent().children('.send_status').remove();
    
    if (files.length > 1) {
        dropZone.after('<p class="send_status lead text-danger">Пожалуйста, выберите один файл!</p>');
        return;
    }

    var file = files[0],
        maxFileSize = 52428800,
        Data = new FormData();

    if (file.size <= maxFileSize) { // && file.type == 'text/csv'
        Data.append('data', file);
    } else {
        dropZone.after('<p class="send_status lead text-danger">Загружаемый файл должен быть в .csv формате и не превышать 50мб!</p>');
        return;
    }

    $.ajax({
        url: dropZone.attr('action'),
        type: dropZone.attr('method'),
        data: Data,
        contentType: false,
        processData: false,
        beforeSend: function() {

            dropZone.after('<p class="send_status lead text-success">Подождите.. файл обрабатывается</p>');
            $('#response').slideUp().html('');
        },
        success: function(json) {
            dropZone.parent().children('.send_status').remove();

            if (json.success) {
                dropZone.after('<p class="send_status lead text-success">Файл успешно загружен!</p>');
                $('#response').html(json.html);
                $('#response').slideDown();
            }

            if (json.error) {
                dropZone.after('<p class="send_status lead text-danger">' + json.msg + '</p>');
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            dropZone.parent().children('.send_status').remove();
            dropZone.after('<p class="send_status lead text-danger">Внутренняя ошибка.</p>');
        }
   });
}